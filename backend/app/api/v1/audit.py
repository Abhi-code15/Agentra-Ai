"""Audit events query and inspection API endpoints."""
import math
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import RoleChecker
from app.db.session import get_db
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.schemas.audit import AuditEventResponse
from app.schemas.common import PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/audit-events", tags=["Audit"])


@router.get("", response_model=PaginatedResponse[AuditEventResponse])
def list_audit_events(
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type"),
    entity_id: Optional[uuid.UUID] = Query(default=None, description="Filter by entity UUID"),
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(RoleChecker(["REVIEWER", "ADMIN"])),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AuditEventResponse]:
    """Returns immutable audit logs (accessible only to REVIEWER and ADMIN)."""
    repo = AuditRepository(db)
    items, total_records = repo.list_events(
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        page=page,
        page_size=page_size,
    )

    total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0
    events_data = [AuditEventResponse.model_validate(e) for e in items]

    return PaginatedResponse(
        data=events_data,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
        ),
    )
