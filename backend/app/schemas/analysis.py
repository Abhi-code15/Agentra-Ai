"""Pydantic schemas for analysis runs, execution steps, and compliance findings."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalysisInitiateResponse(BaseModel):
    analysis_run_id: uuid.UUID
    document_id: uuid.UUID
    status: str
    model_name: str
    started_at: datetime


class AnalysisStepResponse(BaseModel):
    id: uuid.UUID
    step_number: int
    step_type: str
    tool_name: Optional[str] = None
    status: str
    duration_ms: int
    error_code: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FindingResponse(BaseModel):
    id: uuid.UUID
    analysis_run_id: uuid.UUID
    rule_id: Optional[uuid.UUID] = None
    finding_code: str
    title: str
    description: str
    severity: str
    finding_type: str
    evidence: Dict[str, Any]
    confidence_indicator: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalysisDetailResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    requested_by: uuid.UUID
    status: str
    provider: str
    model_name: str
    prompt_version: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    safe_error_message: Optional[str] = None
    findings_count: int = 0
    steps_count: int = 0

    class Config:
        from_attributes = True
