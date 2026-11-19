"""Pydantic structured output schemas for Gemini policy extractions and receipt parsing."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ApprovalTierSchema(BaseModel):
    tier_name: str = Field(description="Name or title of approval level, e.g. Manager, Finance, VP")
    minimum_amount: Optional[float] = Field(default=None, description="Lower bound threshold in currency")
    maximum_amount: Optional[float] = Field(default=None, description="Upper bound threshold in currency")
    approver_role: str = Field(description="Designated approving authority")
    currency: str = Field(default="USD", description="Currency symbol or code")
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


class ExtractedPolicyRuleItemSchema(BaseModel):
    rule_code: str = Field(description="Unique mnemonic identifier e.g. EXP-MEAL-MAX, LEAVE-SICK-DOC, TRAVEL-HOTEL-CAP")
    name: str = Field(description="Clear human-readable rule title")
    description: str = Field(description="Detailed statement of the condition or limitation")
    category: str = Field(description="ELIGIBILITY, LIMIT, DOCUMENTATION, APPROVAL, TIMELINESS, RESTRICTION")
    rule_type: str = Field(description="NUMERIC_LIMIT, CATEGORICAL_ALLOWED, CATEGORICAL_DISALLOWED, MANDATORY_DOCUMENTATION, SUBMISSION_DEADLINE, APPROVAL_TIER")
    limit_amount: Optional[float] = Field(default=None, description="Numeric monetary ceiling or allowance if applicable")
    currency: Optional[str] = Field(default="USD", description="Currency code, e.g. USD, EUR, INR")
    target_category: Optional[str] = Field(default=None, description="Expense or leave type this rule governs, e.g. MEALS, LODGING, SICK_LEAVE")
    required_documents: Optional[List[str]] = Field(default=None, description="List of required receipts or certificates")
    submission_window_days: Optional[int] = Field(default=None, description="Maximum allowable days between event and claim submission")
    approver_role: Optional[str] = Field(default=None, description="Required role if approval tier rule")
    section_reference: Optional[str] = Field(default=None, description="Section heading or clause identifier from document")
    page_number: Optional[int] = Field(default=None, description="Page number in source document")
    verbatim_quote: str = Field(description="Direct verbatim sentence from text establishing this rule")


class EnterprisePolicyRuleExtractionSchema(BaseModel):
    policy_title: str = Field(description="Official title of the policy")
    policy_category: str = Field(description="EXPENSE, LEAVE, TRAVEL, PROCUREMENT, HR, GENERAL")
    effective_date: Optional[str] = Field(default=None, description="Effective start date (YYYY-MM-DD)")
    rules: List[ExtractedPolicyRuleItemSchema] = Field(default_factory=list)
    ambiguities: List[PotentialAmbiguitySchema] = Field(default_factory=list)


class ReceiptClaimItemExtractionSchema(BaseModel):
    merchant_name: Optional[str] = Field(default=None, description="Merchant or vendor name from receipt")
    invoice_number: Optional[str] = Field(default=None, description="Invoice or receipt number")
    transaction_date: Optional[str] = Field(default=None, description="Date on receipt (YYYY-MM-DD)")
    category: str = Field(default="MEALS", description="Inferred category: MEALS, LODGING, TRANSPORT, FLIGHT, SUPPLIES, OTHER")
    total_amount: float = Field(default=0.0, description="Grand total amount on receipt")
    currency: str = Field(default="USD", description="Currency code")
    tax_amount: Optional[float] = Field(default=None, description="Tax or VAT amount")
    line_items: List[Dict[str, Any]] = Field(default_factory=list, description="Sub-items listed on invoice")
    is_receipt_clear: bool = Field(default=True, description="Whether the receipt is legible and valid")
