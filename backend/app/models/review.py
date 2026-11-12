"""SQLAlchemy 2.0 model for human review tasks."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class ReviewTask(Base, TimestampMixin):
    """Human-in-the-Loop review task queued for a compliance finding."""
    __tablename__ = "review_tasks"
    __table_args__ = (
        UniqueConstraint("finding_id", name="uq_review_tasks_finding"),
        CheckConstraint(
            "status IN ('OPEN', 'IN_REVIEW', 'COMPLETED')",
            name="ck_review_tasks_status",
        ),
        CheckConstraint(
            "decision IS NULL OR decision IN ('APPROVED', 'REJECTED', 'NEEDS_REVISION')",
            name="ck_review_tasks_decision",
        ),
        Index("idx_review_tasks_status", "status"),
        Index("idx_review_tasks_assigned_reviewer", "assigned_reviewer_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="OPEN",
        nullable=False,
    )
    decision: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    reviewer_comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    finding: Mapped["Finding"] = relationship("Finding", back_populates="review_task")
    reviewer: Mapped[Optional["User"]] = relationship("User")
