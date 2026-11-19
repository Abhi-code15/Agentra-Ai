"""SQLAlchemy 2.0 models for employee claims, line items, and attached supporting documents."""
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Claim(Base, TimestampMixin):
    """Employee claim request entity (Expense, Leave, Travel, Procurement)."""
    __tablename__ = "claims"
    __table_args__ = (
        CheckConstraint(
            "claim_type IN ('EXPENSE', 'LEAVE', 'TRAVEL', 'PROCUREMENT')",
            name="ck_claims_type",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'EVALUATING', 'EVALUATED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'REVISION_REQUESTED')",
            name="ck_claims_status",
        ),
        Index("idx_claims_org_status", "organization_id", "status"),
        Index("idx_claims_employee", "employee_id"),
        Index("idx_claims_number", "claim_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policies.id", ondelete="SET NULL"),
        nullable=True,
    )
    policy_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policy_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    analysis_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    claim_type: Mapped[str] = mapped_column(
        String(50),
        default="EXPENSE",
        nullable=False,
    )
    claim_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    total_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="USD",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="SUBMITTED",
        nullable=False,
    )
    expense_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    submission_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="claims",
    )
    employee: Mapped["User"] = relationship(
        "User",
        foreign_keys=[employee_id],
        back_populates="claims",
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
    )
    policy: Mapped[Optional["Policy"]] = relationship(
        "Policy",
        back_populates="claims",
    )
    policy_version: Mapped[Optional["PolicyVersion"]] = relationship(
        "PolicyVersion",
        back_populates="claims",
    )
    analysis_run: Mapped[Optional["AnalysisRun"]] = relationship(
        "AnalysisRun",
        foreign_keys=[analysis_run_id],
    )
    line_items: Mapped[List["ClaimLineItem"]] = relationship(
        "ClaimLineItem",
        back_populates="claim",
        cascade="all, delete-orphan",
    )
    claim_documents: Mapped[List["ClaimDocument"]] = relationship(
        "ClaimDocument",
        back_populates="claim",
        cascade="all, delete-orphan",
    )
    findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        back_populates="claim",
        cascade="all, delete-orphan",
    )
    review_tasks: Mapped[List["ReviewTask"]] = relationship(
        "ReviewTask",
        back_populates="claim",
        cascade="all, delete-orphan",
    )


class ClaimLineItem(Base, TimestampMixin):
    """Specific itemized expense or leave period associated with a claim."""
    __tablename__ = "claim_line_items"
    __table_args__ = (
        Index("idx_claim_items_claim_id", "claim_id"),
        Index("idx_claim_items_cat", "category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="USD",
        nullable=False,
    )
    quantity: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    unit: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    transaction_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    extracted_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Relationships
    claim: Mapped["Claim"] = relationship(
        "Claim",
        back_populates="line_items",
    )


class ClaimDocument(Base):
    """Association linking supporting documents/receipts to a claim."""
    __tablename__ = "claim_documents"
    __table_args__ = (
        UniqueConstraint("claim_id", "document_id", name="uq_claim_documents_claim_doc"),
        Index("idx_claim_docs_claim_id", "claim_id"),
        Index("idx_claim_docs_doc_id", "document_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(
        String(50),
        default="RECEIPT",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    claim: Mapped["Claim"] = relationship(
        "Claim",
        back_populates="claim_documents",
    )
    document: Mapped["Document"] = relationship(
        "Document",
    )
