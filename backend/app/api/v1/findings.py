"""Findings query and inspection API endpoints."""
import math
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.user import User
from app.repositories.analysis_repo import AnalysisRepository
from app.schemas.analysis import FindingResponse
from app.schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse

router = APIRouter(prefix="/findings", tags=["Findings"])


@router.get("", response_model=PaginatedResponse[FindingResponse])
def list_findings(
    status: Optional[str] = Query(default=None, description="Filter by finding status"),
    severity: Optional[str] = Query(default=None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    finding_type: Optional[str] = Query(default=None, description="Filter by finding type"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[FindingResponse]:
    """Returns a paginated list of findings with optional status and severity filters."""
    repo = AnalysisRepository(db)
    items, total_records = repo.list_findings(
        status=status,
        severity=severity,
        finding_type=finding_type,
        page=page,
        page_size=page_size,
    )

    total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0
    findings_data = [FindingResponse.model_validate(f) for f in items]

    return PaginatedResponse(
        data=findings_data,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
        ),
    )


@router.get("/{finding_id}", response_model=SuccessResponse[FindingResponse])
def get_finding(
    finding_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[FindingResponse]:
    """Retrieves finding details, evidence quote, and rule reference."""
    repo = AnalysisRepository(db)
    finding = repo.get_finding_by_id(finding_id)
    if not finding:
        raise NotFoundException(
            code="FINDING_NOT_FOUND",
            message="The requested compliance finding was not found.",
        )
    return SuccessResponse(data=FindingResponse.model_validate(finding))
