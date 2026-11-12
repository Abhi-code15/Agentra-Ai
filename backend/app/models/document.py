"""SQLAlchemy 2.0 models for documents and document text extractions."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    """Document metadata entity tracking uploaded policies and lifecycle status."""
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "document_status IN ('UPLOADED', 'PARSING', 'READY_FOR_ANALYSIS', 'OCR_REQUIRED', 'CORRUPT', 'FAILED', 'ARCHIVED')",
            name="ck_documents_status",
        ),
        Index("idx_documents_owner_created", "owner_id", "created_at"),
        Index("idx_documents_status", "document_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    file_extension: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    checksum_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    document_status: Mapped[str] = mapped_column(
        String(50),
        default="UPLOADED",
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="documents")
    extractions: Mapped[List["DocumentExtraction"]] = relationship(
        "DocumentExtraction",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    analyses: Mapped[List["AnalysisRun"]] = relationship(
        "AnalysisRun",
        back_populates="document",
    )


class DocumentExtraction(Base):
    """Raw page-by-page text cache extracted from uploaded files."""
    __tablename__ = "document_extractions"
    __table_args__ = (
        CheckConstraint(
            "extraction_status IN ('COMPLETED', 'FAILED', 'EMPTY')",
            name="ck_extractions_status",
        ),
        Index("idx_extractions_document_id", "document_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    extractor_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    extractor_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    extracted_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    page_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    extraction_status: Mapped[str] = mapped_column(
        String(50),
        default="COMPLETED",
        nullable=False,
    )
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
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
    document: Mapped["Document"] = relationship("Document", back_populates="extractions")
