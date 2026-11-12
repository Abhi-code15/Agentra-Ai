"""SQLAlchemy 2.0 model for compliance findings."""
import uuid
from typing import Any, Dict, Optional
from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Finding(Base, TimestampMixin):
    """Compliance finding entity representing issues identified in document analysis."""
    __tablename__ = "findings"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_findings_severity",
        ),
        CheckConstraint(
            "finding_type IN ('violation', 'missing_requirement', 'ambiguity', 'inconsistency', 'manual_verification')",
            name="ck_findings_type",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'NEEDS_REVISION')",
            name="ck_findings_status",
        ),
        Index("idx_findings_run_id", "analysis_run_id"),
        Index("idx_findings_status_severity", "status", "severity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    finding_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    finding_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    evidence: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    confidence_indicator: Mapped[str] = mapped_column(
        String(50),
        default="HIGH",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="OPEN",
        nullable=False,
    )

    # Relationships
    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="findings")
    rule: Mapped[Optional["ComplianceRule"]] = relationship("ComplianceRule", back_populates="findings")
    review_task: Mapped[Optional["ReviewTask"]] = relationship(
        "ReviewTask",
        back_populates="finding",
        uselist=False,
    )
