"""Employee claims submission, receipt attachment, and deterministic policy evaluation API endpoints."""
import math
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_organization, get_current_user
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.integrations.gemini.client import GeminiClient
from app.models.organization import Organization
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.claim_repo import ClaimRepository
from app.repositories.document_repo import DocumentRepository
from app.repositories.policy_repo import PolicyRepository
from app.schemas.claim import (
    ClaimCreate,
    ClaimDocumentItemResponse,
    ClaimEvaluationFindingResponse,
    ClaimEvaluationResponse,
    ClaimLineItemResponse,
    ClaimResponse,
)
from app.schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse
from app.services.claim_service import ClaimService

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[ClaimResponse])
def submit_claim(
    payload: ClaimCreate,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[ClaimResponse]:
    """Submits an employee claim, attaches receipts, and triggers deterministic evaluation."""
    service = ClaimService(
        claim_repo=ClaimRepository(db),
        policy_repo=PolicyRepository(db),
        document_repo=DocumentRepository(db),
        audit_repo=AuditRepository(db),
    )
    claim = service.submit_claim(
        organization_id=org.id,
        employee=current_user,
        payload=payload,
    )

    line_items_resp = [ClaimLineItemResponse.model_validate(it) for it in claim.line_items]

    findings_resp = []
    if claim.findings:
        for f in claim.findings:
            findings_resp.append(
                ClaimEvaluationFindingResponse(
                    id=f.id,
                    finding_code=f.finding_code,
                    title=f.title,
                    description=f.description,
                    severity=f.severity,
                    finding_type=f.finding_type,
                    confidence_indicator=f.confidence_indicator,
                    status=f.status,
                    policy_rule_code=f.policy_rule.rule_code if f.policy_rule else None,
                    evidence=f.evidence or {},
                )
            )

    docs_resp = []
    if claim.claim_documents:
        for cd in claim.claim_documents:
            docs_resp.append(
                ClaimDocumentItemResponse(
                    id=cd.id,
                    document_id=cd.document_id,
                    document_type=cd.document_type,
                    original_filename=cd.document.original_filename if cd.document else None,
                    file_size_bytes=cd.document.file_size_bytes if cd.document else None,
                    created_at=cd.created_at,
                )
            )

    open_review_task = next((rt for rt in claim.review_tasks if rt.status == "OPEN"), None)
    review_task_id = open_review_task.id if open_review_task else None
    latest_decided_task = next(
        (rt for rt in sorted(claim.review_tasks, key=lambda x: x.decided_at or x.updated_at, reverse=True) if rt.decision is not None),
        None,
    )

    res = ClaimResponse(
        id=claim.id,
        organization_id=claim.organization_id,
        employee_id=claim.employee_id,
        department_id=claim.department_id,
        policy_id=claim.policy_id,
        policy_version_id=claim.policy_version_id,
        analysis_run_id=claim.analysis_run_id,
        claim_type=claim.claim_type,
        claim_number=claim.claim_number,
        title=claim.title,
        description=claim.description,
        total_amount=claim.total_amount,
        currency=claim.currency,
        status=claim.status,
        expense_date=claim.expense_date,
        submission_date=claim.submission_date,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        employee_name=claim.employee.full_name if claim.employee else None,
        employee_email=claim.employee.email if claim.employee else None,
        policy_name=claim.policy.name if claim.policy else None,
        line_items=line_items_resp,
        findings=findings_resp,
        documents=docs_resp,
        review_task_id=review_task_id,
        reviewer_comments=latest_decided_task.reviewer_comments if latest_decided_task else None,
        decided_at=latest_decided_task.decided_at if latest_decided_task else None,
        reviewed_by_name=latest_decided_task.reviewer.full_name if (latest_decided_task and latest_decided_task.reviewer) else None,
        findings_count=len(claim.findings) if claim.findings else 0,
        attached_documents_count=len(claim.claim_documents) if claim.claim_documents else 0,
    )
    return SuccessResponse(data=res)


@router.get("", response_model=PaginatedResponse[ClaimResponse])
def list_claims(
    status: Optional[str] = Query(None),
    claim_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ClaimResponse]:
    """Lists claims within active organization. Employees see own claims; Reviewers/Admins see all."""
    service = ClaimService(
        claim_repo=ClaimRepository(db),
        policy_repo=PolicyRepository(db),
        document_repo=DocumentRepository(db),
        audit_repo=AuditRepository(db),
    )
    items, total = service.list_claims(
        organization_id=org.id,
        user=current_user,
        status=status,
        claim_type=claim_type,
        page=page,
        page_size=page_size,
    )

    resp_list = []
    for c in items:
        line_items_resp = [ClaimLineItemResponse.model_validate(it) for it in c.line_items]
        latest_decided_task = next(
            (rt for rt in sorted(c.review_tasks, key=lambda x: x.decided_at or x.updated_at, reverse=True) if rt.decision is not None),
            None,
        )
        resp_list.append(
            ClaimResponse(
                id=c.id,
                organization_id=c.organization_id,
                employee_id=c.employee_id,
                department_id=c.department_id,
                policy_id=c.policy_id,
                policy_version_id=c.policy_version_id,
                analysis_run_id=c.analysis_run_id,
                claim_type=c.claim_type,
                claim_number=c.claim_number,
                title=c.title,
                description=c.description,
                total_amount=c.total_amount,
                currency=c.currency,
                status=c.status,
                expense_date=c.expense_date,
                submission_date=c.submission_date,
                created_at=c.created_at,
                updated_at=c.updated_at,
                employee_name=c.employee.full_name if c.employee else None,
                employee_email=c.employee.email if c.employee else None,
                policy_name=c.policy.name if c.policy else None,
                line_items=line_items_resp,
                reviewer_comments=latest_decided_task.reviewer_comments if latest_decided_task else None,
                decided_at=latest_decided_task.decided_at if latest_decided_task else None,
                reviewed_by_name=latest_decided_task.reviewer.full_name if (latest_decided_task and latest_decided_task.reviewer) else None,
                findings_count=len(c.findings) if c.findings else 0,
                attached_documents_count=len(c.claim_documents) if c.claim_documents else 0,
            )
        )

    return PaginatedResponse(
        data=resp_list,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_records=total,
            total_pages=math.ceil(total / page_size) if total > 0 else 1,
        ),
    )


@router.get("/{claim_id}", response_model=SuccessResponse[ClaimResponse])
def get_claim_details(
    claim_id: uuid.UUID,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[ClaimResponse]:
    """Retrieves full claim details, itemized breakdown, attached receipts, and compliance findings."""
    service = ClaimService(
        claim_repo=ClaimRepository(db),
        policy_repo=PolicyRepository(db),
        document_repo=DocumentRepository(db),
        audit_repo=AuditRepository(db),
    )
    claim = service.get_claim(claim_id=claim_id, organization_id=org.id, user=current_user)

    line_items_resp = [ClaimLineItemResponse.model_validate(it) for it in claim.line_items]

    findings_resp = []
    if claim.findings:
        for f in claim.findings:
            findings_resp.append(
                ClaimEvaluationFindingResponse(
                    id=f.id,
                    finding_code=f.finding_code,
                    title=f.title,
                    description=f.description,
                    severity=f.severity,
                    finding_type=f.finding_type,
                    confidence_indicator=f.confidence_indicator,
                    status=f.status,
                    policy_rule_code=f.policy_rule.rule_code if f.policy_rule else None,
                    evidence=f.evidence or {},
                )
            )

    docs_resp = []
    if claim.claim_documents:
        for cd in claim.claim_documents:
            docs_resp.append(
                ClaimDocumentItemResponse(
                    id=cd.id,
                    document_id=cd.document_id,
                    document_type=cd.document_type,
                    original_filename=cd.document.original_filename if cd.document else None,
                    file_size_bytes=cd.document.file_size_bytes if cd.document else None,
                    created_at=cd.created_at,
                )
            )

    open_review_task = next((rt for rt in claim.review_tasks if rt.status == "OPEN"), None)
    review_task_id = open_review_task.id if open_review_task else None
    latest_decided_task = next(
        (rt for rt in sorted(claim.review_tasks, key=lambda x: x.decided_at or x.updated_at, reverse=True) if rt.decision is not None),
        None,
    )

    res = ClaimResponse(
        id=claim.id,
        organization_id=claim.organization_id,
        employee_id=claim.employee_id,
        department_id=claim.department_id,
        policy_id=claim.policy_id,
        policy_version_id=claim.policy_version_id,
        analysis_run_id=claim.analysis_run_id,
        claim_type=claim.claim_type,
        claim_number=claim.claim_number,
        title=claim.title,
        description=claim.description,
        total_amount=claim.total_amount,
        currency=claim.currency,
        status=claim.status,
        expense_date=claim.expense_date,
        submission_date=claim.submission_date,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        employee_name=claim.employee.full_name if claim.employee else None,
        employee_email=claim.employee.email if claim.employee else None,
        policy_name=claim.policy.name if claim.policy else None,
        line_items=line_items_resp,
        findings=findings_resp,
        documents=docs_resp,
        review_task_id=review_task_id,
        reviewer_comments=latest_decided_task.reviewer_comments if latest_decided_task else None,
        decided_at=latest_decided_task.decided_at if latest_decided_task else None,
        reviewed_by_name=latest_decided_task.reviewer.full_name if (latest_decided_task and latest_decided_task.reviewer) else None,
        findings_count=len(claim.findings) if claim.findings else 0,
        attached_documents_count=len(claim.claim_documents) if claim.claim_documents else 0,
    )
    return SuccessResponse(data=res)


@router.post("/{claim_id}/evaluate", response_model=SuccessResponse[ClaimEvaluationResponse])
def evaluate_claim_compliance(
    claim_id: uuid.UUID,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[ClaimEvaluationResponse]:
    """Evaluates claim items against active approved company policy rules deterministically."""
    service = ClaimService(
        claim_repo=ClaimRepository(db),
        policy_repo=PolicyRepository(db),
        document_repo=DocumentRepository(db),
        audit_repo=AuditRepository(db),
    )
    evaluation = service.evaluate_claim(claim_id=claim_id, actor=current_user)
    return SuccessResponse(data=evaluation)


@router.post("/parse-receipt", response_model=SuccessResponse[dict])
def parse_receipt_document(
    document_id: uuid.UUID = Query(..., description="ID of uploaded receipt document"),
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[dict]:
    """Parses text from an uploaded receipt and extracts merchant, total, date, and items."""
    doc_repo = DocumentRepository(db)
    extraction = doc_repo.get_extraction_by_document_id(document_id)
    if not extraction or not extraction.extracted_text:
        raise NotFoundException("Document extraction not found or text is empty.")

    gemini_client = GeminiClient()
    parsed = gemini_client.extract_receipt_data(extraction.extracted_text)
    return SuccessResponse(data=parsed.model_dump())
