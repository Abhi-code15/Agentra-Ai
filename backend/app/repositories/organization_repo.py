"""Repository for multi-tenant organizations, departments, and memberships."""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.organization import Department, Organization, OrganizationMember
from app.models.user import User


class OrganizationRepository:
    """Manages tenant isolation containers, departments, and employee memberships."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, organization_id: uuid.UUID) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.id == organization_id)
        return self.db.scalars(stmt).first()

    def get_by_slug(self, slug: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.slug == slug)
        return self.db.scalars(stmt).first()

    def create(self, name: str, slug: str, domain: Optional[str] = None) -> Organization:
        org = Organization(
            name=name,
            slug=slug,
            domain=domain,
            status="ACTIVE",
        )
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)
        return org

    def list_all(self, page: int = 1, page_size: int = 50) -> Tuple[List[Organization], int]:
        count_stmt = select(func.count(Organization.id))
        total = self.db.scalar(count_stmt) or 0

        stmt = (
            select(Organization)
            .order_by(Organization.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt).all())
        return items, total

    def add_member(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str = "EMPLOYEE",
        department_id: Optional[uuid.UUID] = None,
        employee_code: Optional[str] = None,
    ) -> OrganizationMember:
        member = OrganizationMember(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            department_id=department_id,
            employee_code=employee_code,
            status="ACTIVE",
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_membership(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[OrganizationMember]:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        return self.db.scalars(stmt).first()

    def list_members(
        self,
        organization_id: uuid.UUID,
        role: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
    ) -> List[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .options(joinedload(OrganizationMember.user), joinedload(OrganizationMember.department))
            .where(OrganizationMember.organization_id == organization_id)
        )
        if role:
            stmt = stmt.where(OrganizationMember.role == role)
        if department_id:
            stmt = stmt.where(OrganizationMember.department_id == department_id)
        stmt = stmt.order_by(OrganizationMember.joined_at.desc())
        return list(self.db.scalars(stmt).all())

    def create_department(
        self,
        organization_id: uuid.UUID,
        name: str,
        code: Optional[str] = None,
    ) -> Department:
        dept = Department(
            organization_id=organization_id,
            name=name,
            code=code,
        )
        self.db.add(dept)
        self.db.commit()
        self.db.refresh(dept)
        return dept

    def list_departments(self, organization_id: uuid.UUID) -> List[Department]:
        stmt = (
            select(Department)
            .where(Department.organization_id == organization_id)
            .order_by(Department.name.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_or_create_default_org(self, user: User) -> Organization:
        """Ensures a default organization exists and user is assigned ORG_ADMIN."""
        org = self.get_by_slug("default-org")
        if not org:
            org = self.create(name="Default Enterprise Workspace", slug="default-org")

        membership = self.get_membership(org.id, user.id)
        if not membership:
            role = "ORG_ADMIN" if user.role in ("ADMIN", "REVIEWER") else "EMPLOYEE"
            self.add_member(
                organization_id=org.id,
                user_id=user.id,
                role=role,
                employee_code=f"EMP-{str(user.id)[:6].upper()}",
            )
        return org
