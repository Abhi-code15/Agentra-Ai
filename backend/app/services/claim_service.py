"""Service layer managing employee claim submissions and deterministic policy compliance evaluation."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.core.exceptions import BusinessRuleException, NotFoundException, UnauthorizedException
from app.core.logging import logger
from app.models.claim import Claim
from app.models.finding import Finding
from app.models.review import ReviewTask
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.claim_repo import ClaimRepository
from app.repositories.document_repo import DocumentRepository
from app.repositories.policy_repo import PolicyRepository
from app.rules.claim_evaluator import ClaimEvaluator
from app.schemas.claim import ClaimCreate, ClaimEvaluationResponse


class ClaimService:
    """Orchestrates employee claim submission, receipts association, and deterministic policy evaluation."""

    def __init__(
        self,
        claim_repo: ClaimRepository,
        policy_repo: PolicyRepository,
        document_repo: DocumentRepository,
        audit_repo: AuditRepository,
        evaluator: Optional[ClaimEvaluator] = None,
    ):
        self.claim_repo = claim_repo
        self.policy_repo = policy_repo
        self.document_repo = document_repo
        self.audit_repo = audit_repo
        self.evaluator = evaluator or ClaimEvaluator()

    def submit_claim(
        self,
        organization_id: uuid.UUID,
        employee: User,
        payload: ClaimCreate,
    ) -> Claim:
        # Resolve active policy version if policy_id provided
        policy_version_id = payload.policy_version_id
        if payload.policy_id and not policy_version_id:
            active_version = self.policy_repo.get_active_version(
                policy_id=payload.policy_id,
                for_date=payload.expense_date,
            )
            if active_version:
                policy_version_id = active_version.id

        # Calculate total amount from line items if not specified
        calc_total = sum(item.amount for item in payload.line_items) if payload.line_items else (payload.total_amount or 0.0)

        claim = self.claim_repo.create_claim(
            organization_id=organization_id,
            employee_id=employee.id,
            claim_type=payload.claim_type,
            title=payload.title,
            description=payload.description,
            department_id=payload.department_id,
            policy_id=payload.policy_id,
            policy_version_id=policy_version_id,
            expense_date=payload.expense_date,
            total_amount=calc_total,
            currency=payload.currency,
            status="SUBMITTED",
        )

        # Add line items
        for item_data in payload.line_items:
            self.claim_repo.add_line_item(
                claim_id=claim.id,
                category=item_data.category,
                description=item_data.description,
                amount=item_data.amount,
                currency=item_data.currency,
                quantity=item_data.quantity,
                unit=item_data.unit,
                transaction_date=item_data.transaction_date or payload.expense_date,
                extracted_data=item_data.extracted_data,
            )

        # Attach documents
        for doc_id in payload.document_ids:
            self.claim_repo.attach_document(
                claim_id=claim.id,
                document_id=doc_id,
                document_type="RECEIPT",
            )

        self.audit_repo.create_event(
            actor_id=employee.id,
            event_type="CLAIM_SUBMITTED",
            entity_type="Claim",
            entity_id=claim.id,
            request_id=uuid.uuid4(),
            metadata={"claim_number": claim.claim_number, "total_amount": calc_total, "claim_type": claim.claim_type},
        )

        # Run automated deterministic evaluation against approved policy rules
        try:
            self.evaluate_claim(claim.id, employee)
        except Exception as e:
            logger.warning(f"Immediate evaluation failed: {e}")

        return self.claim_repo.get_claim_by_id(claim.id)

    def evaluate_claim(
        self,
        claim_id: uuid.UUID,
        actor: User,
    ) -> ClaimEvaluationResponse:
        claim = self.claim_repo.get_claim_by_id(claim_id)
        if not claim:
            raise NotFoundException(f"Claim {claim_id} not found.")

        # Resolve governing rules from policy version
        policy_rules = []
        applied_policy_name = "Default Global Policy"
        applied_version_number = 1

        if claim.policy_version_id:
            version = self.policy_repo.get_version_by_id(claim.policy_version_id)
            if version:
                policy_rules = version.rules
                applied_version_number = version.version_number
                if version.policy:
                    applied_policy_name = version.policy.name
        elif claim.policy_id:
            version = self.policy_repo.get_active_version(claim.policy_id, claim.expense_date)
            if version:
                policy_rules = version.rules
                applied_version_number = version.version_number
                claim.policy_version_id = version.id
                if version.policy:
                    applied_policy_name = version.policy.name

        # Run deterministic evaluation
        outcome = self.evaluator.evaluate(claim, policy_rules)

        # Persist findings into database
        db_findings: List[Finding] = []
        for f in outcome.findings:
            finding = Finding(
                organization_id=claim.organization_id,
                claim_id=claim.id,
                policy_rule_id=f.rule_id if f.rule_code != "POLICY-UNCONFIGURED" else None,
                finding_code=f.finding_code,
                title=f.title,
                description=f.description,
                severity=f.severity,
                finding_type=f.finding_type,
                confidence_indicator=f.confidence_indicator,
                evidence=f.evidence,
                status="OPEN",
            )
            self.claim_repo.db.add(finding)
            db_findings.append(finding)

        self.claim_repo.db.commit()

        # Update claim status
        new_status = "EVALUATED"
        if outcome.overall_status in ("VIOLATION", "INSUFFICIENT_DATA", "NEEDS_HUMAN_REVIEW"):
            new_status = "IN_REVIEW"

        self.claim_repo.update_claim_status(claim.id, new_status)

        # Queue Human-in-the-Loop review task if review needed
        review_task_id = None
        if new_status == "IN_REVIEW":
            primary_finding_id = db_findings[0].id if db_findings else None
            review_task = ReviewTask(
                organization_id=claim.organization_id,
                claim_id=claim.id,
                finding_id=primary_finding_id,
                status="OPEN",
            )
            self.claim_repo.db.add(review_task)
            self.claim_repo.db.commit()
            self.claim_repo.db.refresh(review_task)
            review_task_id = review_task.id

        self.audit_repo.create_event(
            actor_id=actor.id,
            event_type="CLAIM_EVALUATED",
            entity_type="Claim",
            entity_id=claim.id,
            request_id=uuid.uuid4(),
            metadata={
                "outcome": outcome.overall_status,
                "findings_count": len(db_findings),
                "review_queued": review_task_id is not None,
            },
        )

        return ClaimEvaluationResponse(
            claim_id=claim.id,
            claim_number=claim.claim_number,
            overall_status=new_status,
            evaluation_result=outcome.overall_status,
            total_amount=claim.total_amount,
            currency=claim.currency,
            applied_policy_name=applied_policy_name,
            applied_version_number=applied_version_number,
            findings=[
                {
                    "id": f.id,
                    "finding_code": f.finding_code,
                    "title": f.title,
                    "description": f.description,
                    "severity": f.severity,
                    "finding_type": f.finding_type,
                    "confidence_indicator": f.confidence_indicator,
                    "status": f.status,
                    "policy_rule_code": None,
                    "evidence": f.evidence,
                }
                for f in db_findings
            ],
            violations_count=sum(1 for f in db_findings if f.finding_type == "violation"),
            warnings_count=sum(1 for f in db_findings if f.finding_type != "violation"),
            review_task_id=review_task_id,
        )

    def get_claim(
        self,
        claim_id: uuid.UUID,
        organization_id: uuid.UUID,
        user: User,
    ) -> Claim:
        claim = self.claim_repo.get_claim_by_id(claim_id, organization_id)
        if not claim:
            raise NotFoundException(f"Claim {claim_id} not found in this organization.")

        # Check permission: non-reviewers can only see their own claims
        if user.role not in ("ADMIN", "REVIEWER") and claim.employee_id != user.id:
            raise UnauthorizedException("You do not have permission to view this claim.")

        return claim

    def list_claims(
        self,
        organization_id: uuid.UUID,
        user: User,
        status: Optional[str] = None,
        claim_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Claim], int]:
        if user.role in ("ADMIN", "REVIEWER"):
            return self.claim_repo.list_claims_by_org(
                organization_id=organization_id,
                status=status,
                claim_type=claim_type,
                page=page,
                page_size=page_size,
            )
        else:
            return self.claim_repo.list_claims_by_employee(
                organization_id=organization_id,
                employee_id=user.id,
                page=page,
                page_size=page_size,
            )
