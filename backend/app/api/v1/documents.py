"""Document upload, listing, and inspection API endpoints."""
import math
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentExtractionResponse,
    DocumentSummaryResponse,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[DocumentUploadResponse])
async def upload_document(
    file: UploadFile = File(..., description="PDF or DOCX policy file (max 25MB)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[DocumentUploadResponse]:
    """Uploads a policy document, checks magic bytes, stores privately, and extracts text."""
    file_bytes = await file.read()
    filename = file.filename or "policy_document.pdf"

    service = DocumentService(db)
    document, page_count = service.upload_document(
        filename=filename,
        file_bytes=file_bytes,
        current_user=current_user,
    )

    upload_data = DocumentUploadResponse(
        id=document.id,
        original_filename=document.original_filename,
        mime_type=document.mime_type,
        file_size_bytes=document.file_size_bytes,
        page_count=page_count,
        document_status=document.document_status,
        created_at=document.created_at,
    )
    return SuccessResponse(data=upload_data)


@router.get("", response_model=PaginatedResponse[DocumentSummaryResponse])
def list_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(default=None, description="Optional document_status filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[DocumentSummaryResponse]:
    """Returns a paginated list of documents owned by the user (or all for reviewers)."""
    service = DocumentService(db)
    items, total_records = service.list_documents(
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status,
    )

    total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0
    summaries = [DocumentSummaryResponse.model_validate(doc) for doc in items]

    return PaginatedResponse(
        data=summaries,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
        ),
    )


@router.get("/{document_id}", response_model=SuccessResponse[DocumentDetailResponse])
def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[DocumentDetailResponse]:
    """Returns detailed metadata and text extraction information for a document."""
    service = DocumentService(db)
    document = service.get_document(document_id, current_user)

    extraction = service.doc_repo.get_extraction_by_document_id(document.id)
    extraction_schema = None
    if extraction:
        extraction_schema = DocumentExtractionResponse(
            id=extraction.id,
            document_id=extraction.document_id,
            extractor_name=extraction.extractor_name,
            extractor_version=extraction.extractor_version,
            page_count=extraction.page_count,
            extraction_status=extraction.extraction_status,
            metadata=extraction.metadata_json,
            created_at=extraction.created_at,
        )

    detail_data = DocumentDetailResponse(
        id=document.id,
        owner_id=document.owner_id,
        original_filename=document.original_filename,
        mime_type=document.mime_type,
        file_extension=document.file_extension,
        file_size_bytes=document.file_size_bytes,
        checksum_sha256=document.checksum_sha256,
        document_status=document.document_status,
        created_at=document.created_at,
        updated_at=document.updated_at,
        extraction=extraction_schema,
    )
    return SuccessResponse(data=detail_data)


@router.delete("/{document_id}", response_model=SuccessResponse[dict])
def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[dict]:
    """Soft-deletes a document owned by the user and unlinks its physical file."""
    service = DocumentService(db)
    service.delete_document(document_id, current_user)
    return SuccessResponse(data={"message": "Document successfully deleted."})
