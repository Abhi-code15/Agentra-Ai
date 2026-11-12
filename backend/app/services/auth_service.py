"""Authentication service handling registration, credentials verification, and session rotation."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AgentraException, ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserLoginRequest, UserRegisterRequest


class AuthService:
    """Service orchestrating user identity, authentication, and token rotations."""

    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def register_user(self, payload: UserRegisterRequest) -> User:
        """Registers a new user account, validating email uniqueness and role."""
        existing_user = self.user_repo.get_by_email(payload.email)
        if existing_user:
            raise ConflictException(
                code="AUTH_EMAIL_EXISTS",
                message="An account with this email address already exists.",
            )

        role = payload.role.upper()
        if role not in ("USER", "REVIEWER", "ADMIN"):
            role = "USER"

        password_hash = hash_password(payload.password)
        user = self.user_repo.create_user(
            email=payload.email,
            full_name=payload.full_name,
            password_hash=password_hash,
            role=role,
        )
        return user

    def authenticate_user(
        self,
        payload: UserLoginRequest,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[User, str, str]:
        """Authenticates email/password, issues access token and creates refresh session."""
        user = self.user_repo.get_by_email(payload.email)
        if not user or not user.is_active:
            raise UnauthorizedException(
                code="AUTH_INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )

        if not verify_password(payload.password, user.password_hash):
            raise UnauthorizedException(
                code="AUTH_INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )

        # Generate JWT access token
        access_token = create_access_token(
            subject=str(user.id),
            role=user.role,
        )

        # Generate rotating refresh token and store hash
        raw_refresh_token = generate_opaque_token()
        token_hash = hash_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        self.user_repo.create_refresh_session(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        return user, access_token, raw_refresh_token

    def rotate_refresh_token(
        self,
        raw_refresh_token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Rotates refresh token. Detects replay attacks and revokes token family if reused."""
        token_hash = hash_token(raw_refresh_token)
        session = self.user_repo.get_refresh_session_by_hash(token_hash)

        if not session:
            raise UnauthorizedException(
                code="AUTH_SESSION_INVALID",
                message="Invalid refresh session.",
            )

        # Replay Attack Detection: If token is already revoked, revoke all user sessions
        if session.revoked_at is not None:
            self.user_repo.revoke_all_user_sessions(session.user_id)
            raise UnauthorizedException(
                code="AUTH_SESSION_REVOKED",
                message="Security alert: Refresh token already used. All sessions revoked.",
            )

        # Check Expiry
        if datetime.now(timezone.utc) > session.expires_at:
            self.user_repo.revoke_refresh_session(session.id)
            raise UnauthorizedException(
                code="AUTH_SESSION_EXPIRED",
                message="Refresh session expired. Please log in again.",
            )

        user = self.user_repo.get_by_id(session.user_id)
        if not user or not user.is_active:
            raise UnauthorizedException(
                code="AUTH_USER_INACTIVE",
                message="User account is inactive or deleted.",
            )

        # Mint new access token
        access_token = create_access_token(
            subject=str(user.id),
            role=user.role,
        )

        # Rotate refresh token
        new_raw_refresh_token = generate_opaque_token()
        new_token_hash = hash_token(new_raw_refresh_token)
        new_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_session = self.user_repo.create_refresh_session(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        # Revoke old session and link to replacement
        self.user_repo.revoke_refresh_session(
            session_id=session.id,
            replaced_by_id=new_session.id,
        )

        return access_token, new_raw_refresh_token

    def logout_user(self, raw_refresh_token: Optional[str]) -> None:
        """Revokes the active refresh session."""
        if not raw_refresh_token:
            return
        token_hash = hash_token(raw_refresh_token)
        session = self.user_repo.get_refresh_session_by_hash(token_hash)
        if session and session.revoked_at is None:
            self.user_repo.revoke_refresh_session(session.id)
