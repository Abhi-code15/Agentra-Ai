"""Pydantic schemas for policies, policy versions, and policy rules."""
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PolicyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    category: str = Field(..., description="EXPENSE, LEAVE, TRAVEL, PROCUREMENT, HR, GENERAL")
    description: Optional[str] = None
    department_id: Optional[uuid.UUID] = None


class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    status: Optional[str] = None


class PolicyRuleCreate(BaseModel):
    rule_code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    description: str
    category: str = Field(..., description="ELIGIBILITY, LIMIT, DOCUMENTATION, APPROVAL, TIMELINESS, RESTRICTION")
    rule_type: str = Field(..., description="NUMERIC_LIMIT, CATEGORICAL_ALLOWED, CATEGORICAL_DISALLOWED, MANDATORY_DOCUMENTATION, SUBMISSION_DEADLINE, APPROVAL_TIER")
    rule_definition: Dict[str, Any] = Field(default_factory=dict)
    source_reference: Dict[str, Any] = Field(default_factory=dict)
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class PolicyRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    rule_type: Optional[str] = None
    rule_definition: Optional[Dict[str, Any]] = None
    source_reference: Optional[Dict[str, Any]] = None
    verification_status: Optional[str] = None


class PolicyRuleResponse(BaseModel):
    id: uuid.UUID
    policy_version_id: uuid.UUID
    rule_code: str
    name: str
    description: str
    category: str
    rule_type: str
    rule_definition: Dict[str, Any]
    source_reference: Dict[str, Any]
    extraction_confidence: float
    verification_status: str
    approval_status: str
    created_by: Optional[uuid.UUID] = None
    approved_by: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PolicyVersionResponse(BaseModel):
    id: uuid.UUID
    policy_id: uuid.UUID
    document_id: Optional[uuid.UUID] = None
    version_number: int
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None
    status: str
    extracted_at: Optional[datetime] = None
    approved_by: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    rules_count: int = 0
    document_filename: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PolicyResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    name: str
    category: str
    description: Optional[str] = None
    status: str
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    versions_count: int = 0
    active_version_number: Optional[int] = None

    class Config:
        from_attributes = True


class PolicyDetailResponse(PolicyResponse):
    versions: List[PolicyVersionResponse] = Field(default_factory=list)
    active_rules: List[PolicyRuleResponse] = Field(default_factory=list)


class PolicyVersionDetailResponse(PolicyVersionResponse):
    rules: List[PolicyRuleResponse] = Field(default_factory=list)
