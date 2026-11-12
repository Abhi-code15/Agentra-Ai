"""Common API response envelopes and metadata schemas."""
from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ResponseMeta(BaseModel):
    request_id: Optional[str] = Field(default=None, description="Correlation UUID")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp",
    )


class PaginationMeta(BaseModel):
    page: int = Field(description="Current page (1-based)")
    page_size: int = Field(description="Items per page")
    total_records: int = Field(description="Total count of records")
    total_pages: int = Field(description="Total calculated pages")


class SuccessResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: DataT
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class PaginatedResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: List[DataT]
    pagination: PaginationMeta
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: List[Any] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorPayload
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
