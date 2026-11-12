"""Pydantic schemas for documents and document text extractions."""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DocumentExtractionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    extractor_name: str
    extractor_version: str
    page_count: int
    extraction_status: str
    extracted_text: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size_bytes: int
    page_count: int
    document_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentSummaryResponse(BaseModel):
    id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size_bytes: int
    document_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    original_filename: str
    mime_type: str
    file_extension: str
    file_size_bytes: int
    checksum_sha256: str
    document_status: str
    created_at: datetime
    updated_at: datetime
    extraction: Optional[DocumentExtractionResponse] = None

    class Config:
        from_attributes = True
