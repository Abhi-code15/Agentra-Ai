"""Document and Extraction repository for database persistence."""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentExtraction


class DocumentRepository:
    """Repository managing document metadata and extraction records in PostgreSQL."""

    def __init__(self, db: Session):
        self.db = db

    def create_document(
        self,
        owner_id: uuid.UUID,
        original_filename: str,
        storage_key: str,
        mime_type: str,
        file_extension: str,
        file_size_bytes: int,
        checksum_sha256: str,
        document_status: str = "UPLOADED",
    ) -> Document:
        doc = Document(
            owner_id=owner_id,
            original_filename=original_filename,
            storage_key=storage_key,
            mime_type=mime_type,
            file_extension=file_extension,
            file_size_bytes=file_size_bytes,
            checksum_sha256=checksum_sha256,
            document_status=document_status,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_by_id(
        self,
        document_id: uuid.UUID,
        owner_id: Optional[uuid.UUID] = None,
    ) -> Optional[Document]:
        stmt = select(Document).where(
            Document.id == document_id,
            Document.deleted_at == None,  # noqa: E711
        )
        if owner_id:
            stmt = stmt.where(Document.owner_id == owner_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_documents(
        self,
        owner_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[Document], int]:
        stmt = select(Document).where(Document.deleted_at == None)  # noqa: E711
        if owner_id:
            stmt = stmt.where(Document.owner_id == owner_id)
        if status_filter:
            stmt = stmt.where(Document.document_status == status_filter)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_records = self.db.execute(count_stmt).scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        paginated_stmt = stmt.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
        items = list(self.db.execute(paginated_stmt).scalars().all())

        return items, total_records

    def update_document_status(self, document_id: uuid.UUID, status: str) -> None:
        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(document_status=status)
        )
        self.db.execute(stmt)
        self.db.commit()

    def soft_delete_document(self, document_id: uuid.UUID) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(deleted_at=now, document_status="ARCHIVED")
        )
        self.db.execute(stmt)
        self.db.commit()

    def create_extraction(
        self,
        document_id: uuid.UUID,
        extractor_name: str,
        extractor_version: str,
        extracted_text: str,
        page_count: int,
        extraction_status: str,
        metadata: Dict[str, Any],
    ) -> DocumentExtraction:
        extraction = DocumentExtraction(
            document_id=document_id,
            extractor_name=extractor_name,
            extractor_version=extractor_version,
            extracted_text=extracted_text,
            page_count=page_count,
            extraction_status=extraction_status,
            metadata_json=metadata,
        )
        self.db.add(extraction)
        self.db.commit()
        self.db.refresh(extraction)
        return extraction

    def get_extraction_by_document_id(self, document_id: uuid.UUID) -> Optional[DocumentExtraction]:
        stmt = select(DocumentExtraction).where(DocumentExtraction.document_id == document_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_extractions(self, document_id: uuid.UUID) -> List[DocumentExtraction]:
        stmt = select(DocumentExtraction).where(DocumentExtraction.document_id == document_id)
        return list(self.db.scalars(stmt).all())
