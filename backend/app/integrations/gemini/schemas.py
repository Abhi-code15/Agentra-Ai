"""Pydantic structured output schemas for Gemini policy extractions."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ApprovalTierSchema(BaseModel):
    tier_name: str = Field(description="Name or title of approval level, e.g. Manager, Finance, VP")
    minimum_amount: Optional[float] = Field(default=None, description="Lower bound threshold in currency")
    maximum_amount: Optional[float] = Field(default=None, description="Upper bound threshold in currency")
    approver_role: str = Field(description="Designated approving authority")
    currency: str = Field(default="INR", description="Currency symbol or code")
    source_page: Optional[int] = Field(default=None, description="Page number where defined")
    evidence_quote: str = Field(description="Verbatim sentence from text defining this tier")


class DocumentationRequirementSchema(BaseModel):
    document_name: str = Field(description="Required artifact, e.g. Tax Invoice, Itemized Receipt")
    is_mandatory: bool = Field(default=True, description="Whether this documentation is compulsory")
    submission_window_days: Optional[int] = Field(default=None, description="Submission deadline in days")
    source_page: Optional[int] = Field(default=None, description="Page number where defined")
    evidence_quote: str = Field(description="Verbatim sentence specifying this requirement")


class PotentialAmbiguitySchema(BaseModel):
    description: str = Field(description="Explanation of ambiguous or conflicting clause")
    clause_reference: str = Field(description="Section heading or clause identifier")
    source_page: Optional[int] = Field(default=None, description="Page number where found")
    evidence_quote: str = Field(description="Verbatim quote illustrating ambiguity")
    severity: str = Field(default="MEDIUM", description="Severity: LOW, MEDIUM, or HIGH")


class ExpensePolicyExtractionSchema(BaseModel):
    document_type: str = Field(default="EXPENSE_REIMBURSEMENT_POLICY")
    document_title: str = Field(description="Title of policy extracted from header")
    effective_date: Optional[str] = Field(default=None, description="Effective date (YYYY-MM-DD or null)")
    approval_tiers: List[ApprovalTierSchema] = Field(default_factory=list)
    required_documentation: List[DocumentationRequirementSchema] = Field(default_factory=list)
    potential_ambiguities: List[PotentialAmbiguitySchema] = Field(default_factory=list)
