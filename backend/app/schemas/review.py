"""Pydantic schemas for Human-in-the-Loop review tasks and decisions."""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from app.schemas.analysis import FindingResponse


class ReviewDecisionRequest(BaseModel):
    decision: str = Field(description="Decision: APPROVED, REJECTED, or NEEDS_REVISION")
    reviewer_comments: Optional[str] = Field(default=None, description="Mandatory commentary if rejected")

    @model_validator(mode="after")
    def validate_comments_on_reject(self) -> "ReviewDecisionRequest":
        dec = self.decision.upper()
        if dec not in ("APPROVED", "REJECTED", "NEEDS_REVISION"):
            raise ValueError("Decision must be one of: APPROVED, REJECTED, NEEDS_REVISION")
        if dec == "REJECTED" and (not self.reviewer_comments or not self.reviewer_comments.strip()):
            raise ValueError("Comments are mandatory when rejecting a finding.")
        return self


class ReviewTaskResponse(BaseModel):
    id: uuid.UUID
    finding_id: uuid.UUID
    assigned_reviewer_id: Optional[uuid.UUID] = None
    status: str
    decision: Optional[str] = None
    reviewer_comments: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    finding: Optional[FindingResponse] = None

    class Config:
        from_attributes = True
