"""Append-only audit event repository."""
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


class AuditRepository:
    """Repository handling append-only writes and queries for audit logs."""

    def __init__(self, db: Session):
        self.db = db

    def record_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: uuid.UUID,
        request_id: Optional[uuid.UUID] = None,
        actor_id: Optional[uuid.UUID] = None,
        analysis_run_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        event_metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            actor_id=actor_id,
            organization_id=organization_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            request_id=request_id or uuid.uuid4(),
            analysis_run_id=analysis_run_id,
            event_metadata=event_metadata or {},
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def create_event(
        self,
        event_type: str = "SYSTEM_EVENT",
        entity_type: str = "System",
        entity_id: Optional[uuid.UUID] = None,
        request_id: Optional[uuid.UUID] = None,
        actor_id: Optional[uuid.UUID] = None,
        analysis_run_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        event_metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AuditEvent:
        """Alias for record_event with metadata parameter compatibility."""
        meta = metadata or event_metadata or {}
        eid = entity_id or uuid.uuid4()
        return self.record_event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=eid,
            request_id=request_id or uuid.uuid4(),
            actor_id=actor_id,
            analysis_run_id=analysis_run_id,
            organization_id=organization_id,
            event_metadata=meta,
        )

    def list_events(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        event_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AuditEvent], int]:
        stmt = select(AuditEvent)
        if entity_type:
            stmt = stmt.where(AuditEvent.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(AuditEvent.entity_id == entity_id)
        if event_type:
            stmt = stmt.where(AuditEvent.event_type == event_type)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_records = self.db.execute(count_stmt).scalar() or 0

        offset = (page - 1) * page_size
        paginated_stmt = stmt.order_by(AuditEvent.created_at.desc()).offset(offset).limit(page_size)
        items = list(self.db.execute(paginated_stmt).scalars().all())

        return items, total_records
