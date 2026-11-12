"""Document service orchestrating validation, disk storage, and text extraction."""
import os
import uuid
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AgentraException, ConflictException, ForbiddenException, NotFoundException
from app.models.document import Document
from app.models.user import User
from app.repositories.document_repo import DocumentRepository
from app.storage.local_storage import LocalStorageManager
from app.storage.parsers import extract_text_from_docx, extract_text_from_pdf, validate_magic_bytes


class DocumentService:
    """Service managing document uploads, validation, storage, and text extraction pipelines."""

    def __init__(self, db: Session):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.storage = LocalStorageManager()

    def upload_document(
        self,
        filename: str,
        file_bytes: bytes,
        current_user: User,
    ) -> Tuple[Document, int]:
        """Validates payload, stores securely on disk, and runs text extraction."""
        # 1. File Size Verification
        size = len(file_bytes)
        if size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise AgentraException(
                code="FILE_TOO_LARGE",
                message=f"File exceeds maximum permitted upload limit of {settings.MAX_UPLOAD_SIZE_BYTES} bytes (25MB).",
                status_code=400,
            )

        # 2. Magic Byte Signature Validation
        mime_type = validate_magic_bytes(file_bytes)
        extension = os.path.splitext(filename)[1].lower()
        if not extension:
            extension = ".pdf" if "pdf" in mime_type else ".docx"

        # 3. Secure Disk Storage (generates random UUID filename)
        storage_key, checksum, _ = self.storage.save_file(file_bytes)

        # 4. Insert Initial Document Record
        document = self.doc_repo.create_document(
            owner_id=current_user.id,
            original_filename=filename,
            storage_key=storage_key,
            mime_type=mime_type,
            file_extension=extension,
            file_size_bytes=size,
            checksum_sha256=checksum,
            document_status="PARSING",
        )

        # 5. Execute Text Extraction
        try:
            if "pdf" in mime_type:
                raw_text, page_count, status, metadata = extract_text_from_pdf(file_bytes)
                extractor_name = "PyMuPDF"
                extractor_version = "1.24"
            else:
                raw_text, page_count, status, metadata = extract_text_from_docx(file_bytes)
                extractor_name = "python-docx"
                extractor_version = "1.1"

            if status == "OCR_REQUIRED":
                self.doc_repo.update_document_status(document.id, "OCR_REQUIRED")
                self.doc_repo.create_extraction(
                    document_id=document.id,
                    extractor_name=extractor_name,
                    extractor_version=extractor_version,
                    extracted_text="",
                    page_count=page_count,
                    extraction_status="EMPTY",
                    metadata=metadata,
                )
                document.document_status = "OCR_REQUIRED"
                return document, page_count

            # Normal Text Extraction Completed
            self.doc_repo.create_extraction(
                document_id=document.id,
                extractor_name=extractor_name,
                extractor_version=extractor_version,
                extracted_text=raw_text,
                page_count=page_count,
                extraction_status="COMPLETED",
                metadata=metadata,
            )
            self.doc_repo.update_document_status(document.id, "READY_FOR_ANALYSIS")
            document.document_status = "READY_FOR_ANALYSIS"
            return document, page_count

        except Exception as e:
            self.doc_repo.update_document_status(document.id, "FAILED")
            document.document_status = "FAILED"
            raise AgentraException(
                code="EXTRACTION_FAILED",
                message=f"Failed to extract text from document: {str(e)}",
                status_code=500,
            )

    def get_document(
        self,
        document_id: uuid.UUID,
        current_user: User,
    ) -> Document:
        """Retrieves document detail, enforcing object-level authorization (BOLA defense)."""
        # REVIEWER and ADMIN can view all active documents
        owner_filter = current_user.id if current_user.role.upper() == "USER" else None

        document = self.doc_repo.get_by_id(document_id, owner_id=owner_filter)
        if not document:
            raise NotFoundException(
                code="DOCUMENT_NOT_FOUND",
                message="The requested document was not found or access is denied.",
            )
        return document

    def list_documents(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
    ) -> Tuple[list, int]:
        """Lists documents filtered by ownership for standard users, or all for reviewers."""
        owner_filter = current_user.id if current_user.role.upper() == "USER" else None
        return self.doc_repo.list_documents(
            owner_id=owner_filter,
            page=page,
            page_size=page_size,
            status_filter=status_filter,
        )

    def delete_document(
        self,
        document_id: uuid.UUID,
        current_user: User,
    ) -> None:
        """Soft-deletes a document and unlinks its physical disk payload."""
        owner_filter = current_user.id if current_user.role.upper() != "ADMIN" else None
        document = self.doc_repo.get_by_id(document_id, owner_id=owner_filter)
        if not document:
            raise NotFoundException(
                code="DOCUMENT_NOT_FOUND",
                message="The requested document was not found or access is denied.",
            )

        # Soft delete in DB
        self.doc_repo.soft_delete_document(document_id)

        # Unlink file from disk
        self.storage.delete_file(document.storage_key)
