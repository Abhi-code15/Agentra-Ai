"""Pydantic schemas for employee claims, line items, and compliance evaluations."""
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ClaimLineItemCreate(BaseModel):
    category: str = Field(..., description="MEALS, LODGING, TRANSPORT, FLIGHT, SICK_LEAVE, etc.")
    description: str = Field(..., min_length=2, max_length=255)
    amount: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="USD", max_length=10)
    quantity: Optional[int] = None
    unit: Optional[str] = None
    transaction_date: Optional[date] = None
    extracted_data: Dict[str, Any] = Field(default_factory=dict)


class ClaimLineItemResponse(BaseModel):
    id: uuid.UUID
    claim_id: uuid.UUID
    category: str
    description: str
    amount: float
    currency: str
    quantity: Optional[int] = None
    unit: Optional[str] = None
    transaction_date: Optional[date] = None
    extracted_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClaimCreate(BaseModel):
    claim_type: str = Field(default="EXPENSE", description="EXPENSE, LEAVE, TRAVEL, PROCUREMENT")
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    policy_id: Optional[uuid.UUID] = None
    policy_version_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    expense_date: Optional[date] = None
    total_amount: Optional[float] = None
    currency: str = Field(default="USD", max_length=10)
    line_items: List[ClaimLineItemCreate] = Field(default_factory=list)
    document_ids: List[uuid.UUID] = Field(default_factory=list, description="IDs of uploaded supporting receipts/bills")


class ClaimEvaluationFindingResponse(BaseModel):
    id: uuid.UUID
    finding_code: str
    title: str
    description: str
    severity: str
    finding_type: str
    confidence_indicator: str
    status: str
    policy_rule_code: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)


class ClaimDocumentItemResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    document_type: str
    original_filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    created_at: datetime


class ClaimResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    employee_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    policy_id: Optional[uuid.UUID] = None
    policy_version_id: Optional[uuid.UUID] = None
    analysis_run_id: Optional[uuid.UUID] = None
    claim_type: str
    claim_number: str
    title: str
    description: Optional[str] = None
    total_amount: float
    currency: str
    status: str
    expense_date: Optional[date] = None
    submission_date: datetime
    created_at: datetime
    updated_at: datetime
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None
    policy_name: Optional[str] = None
    line_items: List[ClaimLineItemResponse] = Field(default_factory=list)
    findings: List[ClaimEvaluationFindingResponse] = Field(default_factory=list)
    documents: List[ClaimDocumentItemResponse] = Field(default_factory=list)
    review_task_id: Optional[uuid.UUID] = None
    reviewer_comments: Optional[str] = None
    decided_at: Optional[datetime] = None
    reviewed_by_name: Optional[str] = None
    findings_count: int = 0
    attached_documents_count: int = 0

    class Config:
        from_attributes = True


class ClaimEvaluationResponse(BaseModel):
    claim_id: uuid.UUID
    claim_number: str
    overall_status: str
    evaluation_result: str = Field(description="PASS, VIOLATION, INSUFFICIENT_DATA, NEEDS_HUMAN_REVIEW")
    total_amount: float
    currency: str
    applied_policy_name: str
    applied_version_number: int
    findings: List[ClaimEvaluationFindingResponse] = Field(default_factory=list)
    violations_count: int
    warnings_count: int
    review_task_id: Optional[uuid.UUID] = None
