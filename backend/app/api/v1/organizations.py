"""Multi-tenant organization, department, and membership management endpoints."""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import RoleChecker, get_current_organization, get_current_user
from app.core.exceptions import ConflictException, NotFoundException
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.repositories.organization_repo import OrganizationRepository
from app.repositories.user_repo import UserRepository
from app.schemas.common import SuccessResponse
from app.schemas.organization import (
    DepartmentCreate,
    DepartmentResponse,
    MemberAdd,
    MemberResponse,
    OrganizationCreate,
    OrganizationResponse,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/current", response_model=SuccessResponse[OrganizationResponse])
def get_current_org(
    org: Organization = Depends(get_current_organization),
) -> SuccessResponse[OrganizationResponse]:
    """Retrieves active organization tenant profile."""
    return SuccessResponse(data=OrganizationResponse.model_validate(org))


@router.get("", response_model=SuccessResponse[List[OrganizationResponse]])
def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[List[OrganizationResponse]]:
    """Lists organizations accessible to the current user."""
    repo = OrganizationRepository(db)
    items, _ = repo.list_all(page=1, page_size=100)
    return SuccessResponse(data=[OrganizationResponse.model_validate(item) for item in items])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[OrganizationResponse])
def create_organization(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[OrganizationResponse]:
    """Creates a new enterprise organization tenant and sets current user as ORG_ADMIN."""
    repo = OrganizationRepository(db)
    existing = repo.get_by_slug(payload.slug)
    if existing:
        raise ConflictException(f"Organization slug '{payload.slug}' is already registered.")

    org = repo.create(
        name=payload.name,
        slug=payload.slug,
        domain=payload.domain,
    )
    repo.add_member(
        organization_id=org.id,
        user_id=current_user.id,
        role="ORG_ADMIN",
        employee_code=f"ADM-{str(current_user.id)[:6].upper()}",
    )
    return SuccessResponse(data=OrganizationResponse.model_validate(org))


@router.get("/members", response_model=SuccessResponse[List[MemberResponse]])
def list_org_members(
    role: Optional[str] = Query(None),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
) -> SuccessResponse[List[MemberResponse]]:
    """Lists employee and reviewer members within the active organization."""
    repo = OrganizationRepository(db)
    members = repo.list_members(organization_id=org.id, role=role)
    response_list = []
    for m in members:
        item = MemberResponse(
            id=m.id,
            organization_id=m.organization_id,
            user_id=m.user_id,
            department_id=m.department_id,
            role=m.role,
            employee_code=m.employee_code,
            status=m.status,
            joined_at=m.joined_at,
            user_email=m.user.email if m.user else None,
            user_full_name=m.user.full_name if m.user else None,
        )
        response_list.append(item)
    return SuccessResponse(data=response_list)


@router.post("/members", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[MemberResponse])
def add_org_member(
    payload: MemberAdd,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(RoleChecker(["ADMIN", "REVIEWER"])),
    db: Session = Depends(get_db),
) -> SuccessResponse[MemberResponse]:
    """Adds or invites an employee or reviewer to the active organization."""
    user_repo = UserRepository(db)
    org_repo = OrganizationRepository(db)

    target_user = user_repo.get_by_email(payload.email)
    if not target_user:
        raise NotFoundException(f"User with email '{payload.email}' not found.")

    existing_mem = org_repo.get_membership(org.id, target_user.id)
    if existing_mem:
        raise ConflictException("User is already a member of this organization.")

    mem = org_repo.add_member(
        organization_id=org.id,
        user_id=target_user.id,
        role=payload.role,
        department_id=payload.department_id,
        employee_code=payload.employee_code,
    )
    return SuccessResponse(
        data=MemberResponse(
            id=mem.id,
            organization_id=mem.organization_id,
            user_id=mem.user_id,
            department_id=mem.department_id,
            role=mem.role,
            employee_code=mem.employee_code,
            status=mem.status,
            joined_at=mem.joined_at,
            user_email=target_user.email,
            user_full_name=target_user.full_name,
        )
    )


@router.get("/departments", response_model=SuccessResponse[List[DepartmentResponse]])
def list_departments(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
) -> SuccessResponse[List[DepartmentResponse]]:
    """Lists departments configured for active organization."""
    repo = OrganizationRepository(db)
    depts = repo.list_departments(organization_id=org.id)
    return SuccessResponse(data=[DepartmentResponse.model_validate(d) for d in depts])


@router.post("/departments", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[DepartmentResponse])
def create_department(
    payload: DepartmentCreate,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(RoleChecker(["ADMIN", "REVIEWER"])),
    db: Session = Depends(get_db),
) -> SuccessResponse[DepartmentResponse]:
    """Creates a new organizational department (e.g. Sales, HR, Engineering)."""
    repo = OrganizationRepository(db)
    dept = repo.create_department(
        organization_id=org.id,
        name=payload.name,
        code=payload.code,
    )
    return SuccessResponse(data=DepartmentResponse.model_validate(dept))
