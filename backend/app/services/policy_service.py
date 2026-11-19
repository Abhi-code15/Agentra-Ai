"""Service layer managing enterprise policy lifecycle, rule extraction, and admin verification."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.core.exceptions import BusinessRuleException, NotFoundException, UnauthorizedException
from app.core.logging import logger
from app.integrations.gemini.client import GeminiClient
from app.models.policy import Policy, PolicyRule, PolicyVersion
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.document_repo import DocumentRepository
from app.repositories.policy_repo import PolicyRepository
from app.schemas.policy import PolicyCreate, PolicyRuleUpdate


class PolicyService:
    """Orchestrates policy creation, AI-driven rule extraction, human edits, and version activation."""

    def __init__(
        self,
        policy_repo: PolicyRepository,
        document_repo: DocumentRepository,
        audit_repo: AuditRepository,
        gemini_client: Optional[GeminiClient] = None,
    ):
        self.policy_repo = policy_repo
        self.document_repo = document_repo
        self.audit_repo = audit_repo
        self.gemini_client = gemini_client or GeminiClient()

    def create_policy(
        self,
        organization_id: uuid.UUID,
        user: User,
        payload: PolicyCreate,
        document_id: Optional[uuid.UUID] = None,
    ) -> Tuple[Policy, PolicyVersion]:
        policy = self.policy_repo.create_policy(
            organization_id=organization_id,
            name=payload.name,
            category=payload.category,
            description=payload.description,
            department_id=payload.department_id,
            created_by=user.id,
        )

        version = self.policy_repo.create_policy_version(
            policy_id=policy.id,
            version_number=1,
            document_id=document_id,
            status="DRAFT",
        )

        self.audit_repo.create_event(
            actor_id=user.id,
            event_type="POLICY_CREATED",
            entity_type="Policy",
            entity_id=policy.id,
            request_id=uuid.uuid4(),
            metadata={"name": policy.name, "category": policy.category},
        )

        # If a document was attached with extracted text, trigger rule extraction immediately
        if document_id:
            try:
                self.extract_rules_for_version(version.id, user)
            except Exception as e:
                logger.warning(f"Immediate rule extraction deferred: {e}")

        return policy, version

    def extract_rules_for_version(
        self,
        version_id: uuid.UUID,
        user: User,
    ) -> List[PolicyRule]:
        version = self.policy_repo.get_version_by_id(version_id)
        if not version:
            raise NotFoundException(f"Policy version {version_id} not found.")

        if not version.document_id:
            raise BusinessRuleException("Cannot extract rules: No reference document attached to this policy version.")

        extractions = self.document_repo.get_extractions(version.document_id)
        if not extractions:
            raise BusinessRuleException("Document has no extracted text available. Please parse the document first.")

        document_text = "\n\n".join([ext.extracted_text for ext in extractions if ext.extracted_text])
        if not document_text.strip():
            raise BusinessRuleException("Document extracted text is empty.")

        policy = version.policy
        category = policy.category if policy else "EXPENSE"

        # AI Extraction of structured rules
        extracted_data = self.gemini_client.extract_enterprise_policy_rules(document_text, category)

        # Remove existing unverified/pending rules to allow idempotent re-extraction
        existing_rules = self.policy_repo.list_rules_by_version(version.id)
        for r in existing_rules:
            if r.approval_status != "APPROVED":
                self.policy_repo.db.delete(r)
        self.policy_repo.db.commit()

        existing_codes = {r.rule_code for r in self.policy_repo.list_rules_by_version(version.id)}
        saved_rules: List[PolicyRule] = []
        for item in extracted_data.rules:
            if item.rule_code in existing_codes:
                continue
            existing_codes.add(item.rule_code)
            rule_def = {
                "limit_amount": item.limit_amount,
                "currency": item.currency,
                "target_category": item.target_category,
                "required_documents": item.required_documents,
                "submission_window_days": item.submission_window_days,
                "approver_role": item.approver_role,
            }
            source_ref = {
                "section": item.section_reference,
                "page_number": item.page_number,
                "verbatim_quote": item.verbatim_quote,
            }

            rule = self.policy_repo.create_policy_rule(
                policy_version_id=version.id,
                rule_code=item.rule_code,
                name=item.name,
                description=item.description,
                category=item.category,
                rule_type=item.rule_type,
                rule_definition=rule_def,
                source_reference=source_ref,
                extraction_confidence=1.0,
                created_by=user.id,
            )
            saved_rules.append(rule)

        version.status = "PENDING_APPROVAL"
        version.extracted_at = datetime.now(timezone.utc)
        self.policy_repo.db.commit()

        self.audit_repo.create_event(
            actor_id=user.id,
            event_type="POLICY_RULES_EXTRACTED",
            entity_type="PolicyVersion",
            entity_id=version.id,
            request_id=uuid.uuid4(),
            metadata={"rules_extracted_count": len(saved_rules), "policy_id": str(version.policy_id)},
        )

        return saved_rules

    def update_rule(
        self,
        rule_id: uuid.UUID,
        user: User,
        payload: PolicyRuleUpdate,
    ) -> PolicyRule:
        rule = self.policy_repo.get_rule_by_id(rule_id)
        if not rule:
            raise NotFoundException(f"Policy rule {rule_id} not found.")

        updated = self.policy_repo.update_rule(
            rule_id=rule_id,
            name=payload.name,
            description=payload.description,
            category=payload.category,
            rule_type=payload.rule_type,
            rule_definition=payload.rule_definition,
            source_reference=payload.source_reference,
            verification_status=payload.verification_status,
        )
        return updated

    def approve_rule(
        self,
        rule_id: uuid.UUID,
        user: User,
        decision: str = "APPROVED",
    ) -> PolicyRule:
        rule = self.policy_repo.get_rule_by_id(rule_id)
        if not rule:
            raise NotFoundException(f"Policy rule {rule_id} not found.")

        updated = self.policy_repo.approve_rule(
            rule_id=rule_id,
            approver_id=user.id,
            decision=decision,
        )

        self.audit_repo.create_event(
            actor_id=user.id,
            event_type=f"RULE_{decision}",
            entity_type="PolicyRule",
            entity_id=rule.id,
            request_id=uuid.uuid4(),
            metadata={"rule_code": rule.rule_code, "decision": decision},
        )
        return updated

    def activate_policy_version(
        self,
        version_id: uuid.UUID,
        user: User,
    ) -> PolicyVersion:
        version = self.policy_repo.get_version_by_id(version_id)
        if not version:
            raise NotFoundException(f"Policy version {version_id} not found.")

        rules = self.policy_repo.list_rules_by_version(version_id)
        if not rules:
            raise BusinessRuleException("Cannot activate policy version without extracted rules.")

        # Ensure approved rules exist
        approved_rules = [r for r in rules if r.approval_status == "APPROVED"]
        if not approved_rules:
            # Auto-approve remaining pending rules when activating
            for r in rules:
                if r.approval_status == "PENDING":
                    self.policy_repo.approve_rule(r.id, user.id, "APPROVED")

        activated = self.policy_repo.activate_version(version_id, user.id)

        self.audit_repo.create_event(
            actor_id=user.id,
            event_type="POLICY_VERSION_ACTIVATED",
            entity_type="PolicyVersion",
            entity_id=version.id,
            request_id=uuid.uuid4(),
            metadata={"version_number": version.version_number, "policy_id": str(version.policy_id)},
        )
        return activated
