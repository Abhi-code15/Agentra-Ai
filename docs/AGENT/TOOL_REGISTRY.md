# AGENTRA — Agent Tool Registry & Interface Specifications

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  

---

## 1. Tool Governance Principles

1. **Explicit Schema Validation:** Every tool validates its arguments against strict Pydantic models before execution begins.
2. **Deterministic Side Effects:** Tools that mutate database state (`create_review_finding`) must pass through domain service validation and write audit records.
3. **No Dynamic Execution:** Tools are hardcoded Python classes/functions registered in `ToolRegistry`. Dynamic loading of unknown scripts is forbidden.

---

## 2. Tool 1: `extract_document_information`

- **Purpose:** Extracts structured policy fields (approval tiers, caps, required receipts) from document text using Gemini.
- **Input Contract:**
  ```python
  class ExtractDocumentInfoInput(BaseModel):
      document_id: UUID
      extraction_id: UUID
  ```
- **Output Contract:**
  ```python
  class ExtractDocumentInfoOutput(BaseModel):
      success: bool
      extracted_entities: Dict[str, Any]
      validation_status: str  # VALIDATED, MALFORMED
      error_message: Optional[str] = None
  ```
- **Side Effects:** Writes extracted records to `extracted_items` table.

---

## 3. Tool 2: `retrieve_document_evidence`

- **Purpose:** Searches raw extracted document text for exact matching sentences or section headings supporting a specific compliance inquiry.
- **Input Contract:**
  ```python
  class RetrieveDocumentEvidenceInput(BaseModel):
      document_id: UUID
      search_query: str
      section_keyword: Optional[str] = None
  ```
- **Output Contract:**
  ```python
  class EvidenceMatch(BaseModel):
      page_number: int
      verbatim_quote: str
      confidence_score: float

  class RetrieveDocumentEvidenceOutput(BaseModel):
      matches: List[EvidenceMatch]
      total_matches: int
  ```
- **Side Effects:** Read-only (no database mutations).

---

## 4. Tool 3: `evaluate_compliance_rules`

- **Purpose:** Executes the deterministic Python compliance rule engine against extracted entities to identify gaps or violations.
- **Input Contract:**
  ```python
  class EvaluateComplianceRulesInput(BaseModel):
      analysis_run_id: UUID
      extracted_data: Dict[str, Any]
      rule_category: str = "EXPENSE_REIMBURSEMENT"
  ```
- **Output Contract:**
  ```python
  class RuleEvaluationOutcome(BaseModel):
      rule_code: str
      rule_id: UUID
      status: str  # PASS, FAIL, INSUFFICIENT_DATA, NEEDS_REVIEW
      observed_value: Any
      expected_value: Any
      evidence_quote: Optional[str]
      explanation: str

  class EvaluateComplianceRulesOutput(BaseModel):
      evaluations: List[RuleEvaluationOutcome]
      passed_count: int
      failed_count: int
      needs_review_count: int
  ```
- **Side Effects:** In-memory rule evaluation; returns results to orchestrator.

---

## 5. Tool 4: `create_review_finding`

- **Purpose:** Persists an identified compliance finding into `findings` and queues an active task in `review_tasks`.
- **Input Contract:**
  ```python
  class CreateReviewFindingInput(BaseModel):
      analysis_run_id: UUID
      rule_id: Optional[UUID] = None
      finding_code: str
      title: str
      description: str
      severity: str  # LOW, MEDIUM, HIGH, CRITICAL
      finding_type: str  # violation, missing_requirement, ambiguity, inconsistency, manual_verification
      evidence: Dict[str, Any]
  ```
- **Output Contract:**
  ```python
  class CreateReviewFindingOutput(BaseModel):
      finding_id: UUID
      review_task_id: UUID
      status: str  # PENDING_REVIEW
  ```
- **Side Effects:** Inserts records into `findings` and `review_tasks`; emits `FINDING_CREATED` audit event.
