"""SQLAlchemy 2.0 models for analysis runs, agent execution steps, and extracted items."""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AnalysisRun(Base):
    """Analysis run representing an execution of the agent and compliance engine."""
    __tablename__ = "analysis_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('INITIALIZED', 'RUNNING', 'COMPLETED', 'FAILED', 'TIMED_OUT')",
            name="ck_analysis_runs_status",
        ),
        Index("idx_analysis_runs_document_created", "document_id", "created_at"),
        Index("idx_analysis_runs_requested_by", "requested_by"),
        Index("idx_analysis_runs_user_status", "requested_by", "status"),
        Index("idx_analysis_runs_org_id", "organization_id"),
        Index("idx_analysis_runs_claim_id", "claim_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=True,
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="INITIALIZED",
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(100),
        default="google_genai",
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        default="gemini-2.5-flash",
        nullable=False,
    )
    prompt_version: Mapped[str] = mapped_column(
        String(50),
        default="v1.0.0",
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    safe_error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    execution_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    document: Mapped[Optional["Document"]] = relationship("Document", back_populates="analyses")
    organization: Mapped[Optional["Organization"]] = relationship("Organization")
    claim: Mapped[Optional["Claim"]] = relationship("Claim", foreign_keys=[claim_id])
    user: Mapped["User"] = relationship("User")
    steps: Mapped[List["AnalysisStep"]] = relationship(
        "AnalysisStep",
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        order_by="AnalysisStep.step_number",
    )
    extracted_items: Mapped[List["ExtractedItem"]] = relationship(
        "ExtractedItem",
        back_populates="analysis_run",
        cascade="all, delete-orphan",
    )
    findings: Mapped[List["Finding"]] = relationship(
        "Finding",
        back_populates="analysis_run",
    )


class AnalysisStep(Base):
    """Execution step telemetry recording tool calls, duration, and observations."""
    __tablename__ = "analysis_steps"
    __table_args__ = (
        UniqueConstraint("analysis_run_id", "step_number", name="uq_analysis_steps_run_step"),
        CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED')",
            name="ck_analysis_steps_status",
        ),
        Index("idx_analysis_steps_run_step", "analysis_run_id", "step_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    step_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    tool_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    input_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    output_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        nullable=False,
    )
    duration_ms: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    error_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="steps")


class ExtractedItem(Base):
    """Structured information extracted from document text by Gemini."""
    __tablename__ = "extracted_items"
    __table_args__ = (
        CheckConstraint(
            "validation_status IN ('VALIDATED', 'UNVALIDATED', 'MALFORMED')",
            name="ck_extracted_items_status",
        ),
        Index("idx_extracted_items_run", "analysis_run_id"),
        Index("idx_extracted_items_type", "item_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    item_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    extracted_value: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    source_page: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    evidence_quote: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    evidence_location: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    validation_status: Mapped[str] = mapped_column(
        String(50),
        default="VALIDATED",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="extracted_items")
