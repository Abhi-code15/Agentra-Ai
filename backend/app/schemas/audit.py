"""Pydantic schemas for audit events."""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    event_type: str
    entity_type: str
    entity_id: uuid.UUID
    request_id: uuid.UUID
    analysis_run_id: Optional[uuid.UUID] = None
    event_metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
