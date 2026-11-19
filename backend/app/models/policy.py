"""SQLAlchemy 2.0 models for enterprise policies, policy versions, and extracted policy rules."""
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Policy(Base, TimestampMixin):
    """Company-approved policy standard entity (e.g., Expense Reimbursement, Leave, Travel)."""
    __tablename__ = "policies"
    __table_args__ = (
        CheckConstraint(
            "category IN ('EXPENSE', 'LEAVE', 'TRAVEL', 'PROCUREMENT', 'HR', 'GENERAL')",
            name="ck_policies_category",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'ACTIVE', 'ARCHIVED')",
            name="ck_policies_status",
        ),
        Index("idx_policies_org_cat", "organization_id", "category"),
        Index("idx_policies_status", "status"),
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
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="DRAFT",
        nullable=False,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="policies",
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        back_populates="policies",
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
    )
    versions: Mapped[List["PolicyVersion"]] = relationship(
        "PolicyVersion",
        back_populates="policy",
        cascade="all, delete-orphan",
        order_by="PolicyVersion.version_number.desc()",
    )
    claims: Mapped[List["Claim"]] = relationship(
        "Claim",
        back_populates="policy",
    )


class PolicyVersion(Base, TimestampMixin):
    """Immutable version of a policy, linking extracted rules to an uploaded official document."""
    __tablename__ = "policy_versions"
    __table_args__ = (
        UniqueConstraint("policy_id", "version_number", name="uq_policy_versions_policy_num"),
        CheckConstraint(
            "status IN ('DRAFT', 'PROCESSING', 'PENDING_APPROVAL', 'APPROVED', 'ACTIVE', 'SUPERSEDED', 'ARCHIVED')",
            name="ck_policy_versions_status",
        ),
        Index("idx_policy_versions_dates", "effective_from", "effective_until"),
        Index("idx_policy_versions_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    effective_from: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    effective_until: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="DRAFT",
        nullable=False,
    )
    extracted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    policy: Mapped["Policy"] = relationship(
        "Policy",
        back_populates="versions",
    )
    document: Mapped[Optional["Document"]] = relationship(
        "Document",
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by],
    )
    rules: Mapped[List["PolicyRule"]] = relationship(
        "PolicyRule",
        back_populates="policy_version",
        cascade="all, delete-orphan",
    )
    claims: Mapped[List["Claim"]] = relationship(
        "Claim",
        back_populates="policy_version",
    )


class PolicyRule(Base, TimestampMixin):
    """Structured rule extracted from a policy document and verified/approved by company admin."""
    __tablename__ = "policy_rules"
    __table_args__ = (
        UniqueConstraint("policy_version_id", "rule_code", name="uq_policy_rules_version_code"),
        CheckConstraint(
            "category IN ('ELIGIBILITY', 'LIMIT', 'DOCUMENTATION', 'APPROVAL', 'TIMELINESS', 'RESTRICTION')",
            name="ck_policy_rules_category",
        ),
        CheckConstraint(
            "rule_type IN ('NUMERIC_LIMIT', 'CATEGORICAL_ALLOWED', 'CATEGORICAL_DISALLOWED', 'MANDATORY_DOCUMENTATION', 'SUBMISSION_DEADLINE', 'APPROVAL_TIER')",
            name="ck_policy_rules_type",
        ),
        CheckConstraint(
            "verification_status IN ('UNVERIFIED', 'VERIFIED', 'MODIFIED')",
            name="ck_policy_rules_verification",
        ),
        CheckConstraint(
            "approval_status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_policy_rules_approval",
        ),
        Index("idx_policy_rules_version", "policy_version_id"),
        Index("idx_policy_rules_status", "approval_status", "verification_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    policy_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policy_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    rule_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    rule_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    rule_definition: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    source_reference: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    extraction_confidence: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    verification_status: Mapped[str] = mapped_column(
        String(50),
        default="UNVERIFIED",
        nullable=False,
    )
    approval_status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        nullable=False,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    policy_version: Mapped["PolicyVersion"] = relationship(
        "PolicyVersion",
        back_populates="rules",
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by],
    )
    findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        back_populates="policy_rule",
    )
