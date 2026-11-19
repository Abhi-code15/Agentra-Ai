"""Policy management, AI rule extraction, and human rule approval API endpoints."""
import math
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import RoleChecker, get_current_organization, get_current_user
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.document_repo import DocumentRepository
from app.repositories.policy_repo import PolicyRepository
from app.schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse
from app.schemas.policy import (
    PolicyCreate,
    PolicyDetailResponse,
    PolicyResponse,
    PolicyRuleResponse,
    PolicyRuleUpdate,
    PolicyVersionDetailResponse,
    PolicyVersionResponse,
)
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[PolicyResponse])
def create_policy(
    payload: PolicyCreate,
    document_id: Optional[uuid.UUID] = Query(None, description="Optional ID of uploaded policy document"),
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(RoleChecker(["ADMIN", "REVIEWER"])),
    db: Session = Depends(get_db),
) -> SuccessResponse[PolicyResponse]:
    """Creates a new company standard policy and initializes version 1."""
    service = PolicyService(
        policy_repo=PolicyRepository(db),
        document_repo=DocumentRepository(db),
        audit_repo=AuditRepository(db),
    )
    policy, version = service.create_policy(
        organization_id=org.id,
        user=current_user,
        payload=payload,
        document_id=document_id,
    )
    res = PolicyResponse(
        id=policy.id,
        organization_id=policy.organization_id,
        department_id=policy.department_id,
        name=policy.name,
        category=policy.category,
        description=policy.description,
        status=policy.status,
        created_by=policy.created_by,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
        versions_count=len(policy.versions) if policy.versions else 1,
        active_version_number=1 if policy.status == "ACTIVE" else None,
    )
    return SuccessResponse(data=res)


@router.get("", response_model=PaginatedResponse[PolicyResponse])
def list_policies(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PolicyResponse]:
    """Lists company standard policies for active organization tenant."""
    repo = PolicyRepository(db)
    items, total = repo.list_policies_by_org(
        organization_id=org.id,
        category=category,
        status=status,
        page=page,
        page_size=page_size,
    )

    resp_list = []
    for p in items:
        active_ver = next((v.version_number for v in p.versions if v.status == "ACTIVE"), None)
        resp_list.append(
            PolicyResponse(
                id=p.id,
                organization_id=p.organization_id,
                department_id=p.department_id,
                name=p.name,
                category=p.category,
                description=p.description,
                status=p.status,
                created_by=p.created_by,
                created_at=p.created_at,
                updated_at=p.updated_at,
                versions_count=len(p.versions),
                active_version_number=active_ver,
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


@router.get("/{policy_id}", response_model=SuccessResponse[PolicyDetailResponse])
def get_policy(
    policy_id: uuid.UUID,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[PolicyDetailResponse]:
    """Retrieves policy details, version history, and active benchmark rules."""
    repo = PolicyRepository(db)
    policy = repo.get_policy_by_id(policy_id, organization_id=org.id)
    if not policy:
        raise NotFoundException(f"Policy {policy_id} not found.")

    versions_resp = []
    for v in policy.versions:
        versions_resp.append(
            PolicyVersionResponse(
                id=v.id,
                policy_id=v.policy_id,
                document_id=v.document_id,
                version_number=v.version_number,
                effective_from=v.effective_from,
                effective_until=v.effective_until,
                status=v.status,
                extracted_at=v.extracted_at,
                approved_by=v.approved_by,
                approved_at=v.approved_at,
                rules_count=len(v.rules) if v.rules else 0,
                document_filename=v.document.original_filename if v.document else None,
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
        )

    active_v = next((v for v in policy.versions if v.status == "ACTIVE"), None)
    active_rules = []
    if active_v:
        active_rules = [PolicyRuleResponse.model_validate(r) for r in active_v.rules]

    detail = PolicyDetailResponse(
        id=policy.id,
        organization_id=policy.organization_id,
        department_id=policy.department_id,
        name=policy.name,
        category=policy.category,
        description=policy.description,
        status=policy.status,
        created_by=policy.created_by,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
        versions_count=len(policy.versions),
        active_version_number=active_v.version_number if active_v else None,
        versions=versions_resp,
        active_rules=active_rules,
    )
    return SuccessResponse(data=detail)


@router.get("/versions/{version_id}", response_model=SuccessResponse[PolicyVersionDetailResponse])
def get_policy_version_detail(
    version_id: uuid.UUID,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[PolicyVersionDetailResponse]:
    """Retrieves all rules, citations, and status for a specific policy version."""
    repo = PolicyRepository(db)
    v = repo.get_version_by_id(version_id)
    if not v:
        raise NotFoundException(f"Policy version {version_id} not found.")

    rules_resp = [PolicyRuleResponse.model_validate(r) for r in v.rules]
    return SuccessResponse(
        data=PolicyVersionDetailResponse(
            id=v.id,
            policy_id=v.policy_id,
            document_id=v.document_id,
            version_number=v.version_number,
            effective_from=v.effective_from,
            effective_until=v.effective_until,
            status=v.status,
            extracted_at=v.extracted_at,
            approved_by=v.approved_by,
            approved_at=v.approved_at,
            rules_count=len(v.rules),
            document_filename=v.document.original_filename if v.document else None,
            created_at=v.created_at,
            updated_at=v.updated_at,
            rules=rules_resp,
        )
    )


@router.post("/versions/{version_id}/extract", response_model=SuccessResponse[List[PolicyRuleResponse]])
def extract_rules_from_version_document(
    version_id: uuid.UUID,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(RoleChecker(["ADMIN", "REVIEWER"])),
    db: Session = Depends(get_db),
) -> SuccessResponse[List[PolicyRuleResponse]]:
    """Triggers AI rule extraction from the attached policy standard document."""
    service = PolicyService(
        policy_repo=PolicyRepository(db),
        document_repo=DocumentRepository(db),
        audit_repo=AuditRepository(db),
    )
    rules = service.extract_rules_for_version(version_id=version_id, user=current_user)
    return SuccessResponse(data=[PolicyRuleResponse.model_validate(r) for r in rules])


@router.put("/rules/{rule_id}", response_model=SuccessResponse[PolicyRuleResponse])
def update_policy_rule(
    rule_id: uuid.UUID,
    payload: PolicyRuleUpdate,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(RoleChecker(["ADMIN", "REVIEWER"])),
    db: Session = Depends(get_db),
) -> SuccessResponse[PolicyRuleResponse]:
    """Allows company admin to edit extracted rule values, allowances, and categories."""
    service = PolicyService(
        policy_repo=PolicyRepository(db),
        document_repo=DocumentRepository(db),
        audit_repo=AuditRepository(db),
    )
    updated = service.update_rule(rule_id=rule_id, user=current_user, payload=payload)
    return SuccessResponse(data=PolicyRuleResponse.model_validate(updated))


@router.post("/rules/{rule_id}/approve", response_model=SuccessResponse[PolicyRuleResponse])
def approve_policy_rule(
    rule_id: uuid.UUID,
    decision: str = Query("APPROVED", pattern="^(APPROVED|REJECTED)$"),
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(RoleChecker(["ADMIN", "REVIEWER"])),
    db: Session = Depends(get_db),
) -> SuccessResponse[PolicyRuleResponse]:
    """Company admin verifies and approves/rejects an extracted policy rule."""
    service = PolicyService(
        policy_repo=PolicyRepository(db),
        document_repo=DocumentRepository(db),
        audit_repo=AuditRepository(db),
    )
    approved = service.approve_rule(rule_id=rule_id, user=current_user, decision=decision)
    return SuccessResponse(data=PolicyRuleResponse.model_validate(approved))


@router.post("/versions/{version_id}/activate", response_model=SuccessResponse[PolicyVersionResponse])
def activate_policy_version(
    version_id: uuid.UUID,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(RoleChecker(["ADMIN", "REVIEWER"])),
    db: Session = Depends(get_db),
) -> SuccessResponse[PolicyVersionResponse]:
    """Activates policy version as the official enterprise compliance reference standard."""
    service = PolicyService(
        policy_repo=PolicyRepository(db),
        document_repo=DocumentRepository(db),
        audit_repo=AuditRepository(db),
    )
    version = service.activate_policy_version(version_id=version_id, user=current_user)
    return SuccessResponse(data=PolicyVersionResponse.model_validate(version))
