"""User and RefreshSession repository for database persistence."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.user import RefreshSession, User


class UserRepository:
    """Repository handling all database interactions for users and refresh sessions."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        normalized = email.strip().lower()
        stmt = select(User).where(User.email == normalized)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_user(
        self,
        email: str,
        full_name: str,
        password_hash: str,
        role: str = "USER",
    ) -> User:
        user = User(
            email=email.strip().lower(),
            full_name=full_name.strip(),
            password_hash=password_hash,
            role=role.upper(),
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_refresh_session(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> RefreshSession:
        session = RefreshSession(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_refresh_session_by_hash(self, token_hash: str) -> Optional[RefreshSession]:
        stmt = select(RefreshSession).where(RefreshSession.token_hash == token_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def revoke_refresh_session(
        self,
        session_id: uuid.UUID,
        replaced_by_id: Optional[uuid.UUID] = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshSession)
            .where(RefreshSession.id == session_id)
            .values(revoked_at=now, replaced_by_session_id=replaced_by_id)
        )
        self.db.execute(stmt)
        self.db.commit()

    def revoke_all_user_sessions(self, user_id: uuid.UUID) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshSession)
            .where(RefreshSession.user_id == user_id, RefreshSession.revoked_at == None)  # noqa: E711
            .values(revoked_at=now)
        )
        self.db.execute(stmt)
        self.db.commit()
