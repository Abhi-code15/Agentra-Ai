"""FastAPI authentication and role authorization dependencies."""
import uuid
from typing import List, Optional
from fastapi import Depends, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.models.organization import Organization
from app.repositories.organization_repo import OrganizationRepository
from app.repositories.user_repo import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependency extracting and verifying the authenticated user from the Bearer JWT."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException(
            code="AUTH_TOKEN_MISSING",
            message="Authentication credentials were not provided.",
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(
            code="AUTH_TOKEN_INVALID",
            message="Token payload is missing subject identity.",
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException(
            code="AUTH_TOKEN_INVALID",
            message="Token subject is not a valid UUID.",
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedException(
            code="AUTH_USER_NOT_FOUND",
            message="User account does not exist or is inactive.",
        )

    return user


def get_current_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
) -> Organization:
    """Resolves the current organization tenant context, ensuring strict tenant isolation."""
    org_repo = OrganizationRepository(db)

    if x_organization_id:
        try:
            org_id = uuid.UUID(x_organization_id)
            org = org_repo.get_by_id(org_id)
            if org:
                # Check user has access to this organization
                membership = org_repo.get_membership(org.id, current_user.id)
                if membership or current_user.role == "ADMIN":
                    return org
        except ValueError:
            pass

    # Fallback to default organization associated with the user
    return org_repo.get_or_create_default_org(current_user)


class RoleChecker:
    """Dependency validating that the authenticated user possesses an authorized role."""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = [r.upper() for r in allowed_roles]

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.upper() not in self.allowed_roles:
            raise ForbiddenException(
                code="FORBIDDEN_INSUFFICIENT_ROLE",
                message=f"Access denied. Requires one of roles: {', '.join(self.allowed_roles)}.",
            )
        return current_user
