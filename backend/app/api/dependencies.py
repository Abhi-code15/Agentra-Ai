"""FastAPI authentication and role authorization dependencies."""
import uuid
from typing import List
from fastapi import Depends, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
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
