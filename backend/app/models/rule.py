"""SQLAlchemy 2.0 model for compliance rules."""
import uuid
from typing import Any, Dict, List
from sqlalchemy import Boolean, CheckConstraint, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class ComplianceRule(Base, TimestampMixin):
    """Deterministic compliance rule entity."""
    __tablename__ = "compliance_rules"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_compliance_rules_severity",
        ),
        Index("idx_compliance_rules_category", "category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    rule_code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
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
        String(100),
        default="EXPENSE_REIMBURSEMENT",
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(50),
        default="HIGH",
        nullable=False,
    )
    rule_definition: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # Relationships
    findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        back_populates="rule",
    )
