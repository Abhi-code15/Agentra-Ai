# AGENTRA — Engineering Requirements Specification

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  
**Target:** MVP Implementation  

---

## 1. Functional Requirements Matrix

| Requirement ID | Module | Feature | Priority | Business Rule / Description |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-AUTH-01** | Auth | User Registration | P0 | Validate unique normalized email, password length $\ge 8$, full name. Store Argon2id hash. Default role: `USER`. |
| **REQ-AUTH-02** | Auth | User Login | P0 | Verify email/password. Return generic error on failure. Issue JWT access token in response + rotate refresh token in HttpOnly cookie. |
| **REQ-AUTH-03** | Auth | Session Refresh | P0 | Ingest refresh token from cookie, look up non-revoked session, rotate with new refresh token hash, return fresh access token. |
| **REQ-AUTH-04** | Auth | Logout | P0 | Revoke active refresh session in database, clear cookie, record audit event. |
| **REQ-AUTH-05** | Auth | Role-Based Access | P0 | Enforce roles (`USER`, `REVIEWER`). Protect endpoints using FastAPI dependencies. |
| **REQ-DOC-01** | Documents | Upload & Validation | P0 | Accept `.pdf` and `.docx`. Max file size 25 MB. Validate MIME & magic bytes. Store on disk via UUID key. Compute SHA-256. |
| **REQ-DOC-02** | Documents | Text Extraction | P0 | Extract page-by-page (PyMuPDF for PDF, python-docx for DOCX). Detect scanned/empty files and emit `OCR_REQUIRED`. |
| **REQ-DOC-03** | Documents | Document Listing | P0 | Return paginated list of documents owned by the calling user. REVIEWER can list all documents pending review. |
| **REQ-DOC-04** | Documents | Document Deletion | P0 | Soft delete document record, unlink physical file securely, create audit event. Prevent deletion if active review exists. |
| **REQ-AI-01** | AI Service | Gemini Client | P0 | Dedicated client wrapping Google Gen AI SDK. Configurable model (`gemini-2.5-flash`), timeout (30s), retries with exponential backoff. |
| **REQ-AI-02** | AI Service | Structured Extraction | P0 | Ingest raw extracted text, enforce Pydantic output schema, extract policy limits, roles, documentation requirements, and quotes. |
| **REQ-AI-03** | AI Service | Prompt Injection Defense | P0 | Strict prompt separation with boundary delimiters `<untrusted_policy_content>`. Document text is never treated as executable instruction. |
| **REQ-AGENT-01** | Agent | State Machine | P0 | Finite state orchestrator tracking `current_step`, `step_count` ($\le 6$), inputs, tool invocations, and findings. |
| **REQ-AGENT-02** | Agent | Tool Execution | P0 | Controlled sandbox execution for 4 tools: `extract_document_information`, `retrieve_document_evidence`, `evaluate_compliance_rules`, `create_review_finding`. |
| **REQ-AGENT-03** | Agent | Step Audit Log | P0 | Persist every step execution in `analysis_steps` with sanitized inputs/outputs, latency, and status. |
| **REQ-RULE-01** | Rules | Rule Storage & Seeding| P0 | Seed standard Expense Policy rules in `compliance_rules` table. Rules store structured JSON condition definitions. |
| **REQ-RULE-02** | Rules | Deterministic Evaluator| P0 | Python engine evaluating conditions using allowlisted operators (`equals`, `less_than_or_equal`, `greater_than`, `contains`, `exists`). |
| **REQ-RULE-03** | Rules | Finding Generation | P0 | Produce findings typed as `violation`, `missing_requirement`, `ambiguity`, `inconsistency`, or `manual_verification`. |
| **REQ-REV-01** | Reviews | Task Queue | P0 | Create `review_tasks` for findings requiring human approval. List pending reviews filtered by severity and status. |
| **REQ-REV-02** | Reviews | Decision Execution | P0 | Allow `REVIEWER` to set status: `APPROVED`, `REJECTED`, or `NEEDS_REVISION`. Require comments on rejection. Write audit event. |
| **REQ-AUDIT-01** | Audit | Immutable Logging | P0 | Append-only `audit_events` recording all auth events, uploads, deletions, analyses, and review verdicts with correlation ID. |

---

## 2. Input / Output & Contract Specifications

### 2.1 Expense Policy Analysis Extraction Contract
```json
{
  "document_type": "EXPENSE_REIMBURSEMENT_POLICY",
  "document_title": "string",
  "effective_date": "YYYY-MM-DD or null",
  "approval_tiers": [
    {
      "tier_name": "string",
      "minimum_amount": "number or null",
      "maximum_amount": "number or null",
      "approver_role": "string",
      "currency": "INR",
      "source_page": "integer",
      "evidence_quote": "string"
    }
  ],
  "required_documentation": [
    {
      "document_name": "string",
      "is_mandatory": true,
      "submission_window_days": "integer or null",
      "source_page": "integer",
      "evidence_quote": "string"
    }
  ],
  "clauses": [
    {
      "clause_id": "string",
      "section_title": "string",
      "summary": "string",
      "source_page": "integer",
      "raw_quote": "string"
    }
  ],
  "potential_ambiguities": [
    {
      "description": "string",
      "clause_reference": "string",
      "source_page": "integer",
      "evidence_quote": "string",
      "severity": "LOW | MEDIUM | HIGH"
    }
  ]
}
```

### 2.2 Compliance Rule Evaluation Contract
```json
{
  "rule_code": "EXP_RULE_001",
  "rule_version": 1,
  "status": "PASS | FAIL | INSUFFICIENT_DATA | NEEDS_REVIEW",
  "condition_results": [
    {
      "field": "approval_tiers.maximum_amount",
      "operator": "less_than_or_equal",
      "expected": 5000,
      "observed": 5000,
      "satisfied": true
    }
  ],
  "evidence_references": [
    {
      "page": 2,
      "quote": "Expenses up to INR 5,000 may be approved by the Department Manager."
    }
  ],
  "explanation": "Rule satisfied: Manager tier limit matches policy threshold."
}
```

---

## 3. Business Invariant Rules

1. **User Separation:** A standard `USER` can never retrieve, analyze, or delete documents owned by another user. Response on forbidden access must return `404 NOT FOUND` (or `403 FORBIDDEN` where ownership cannot be leaked).
2. **Reviewer Impartiality:** A user cannot act as a `REVIEWER` on a document or finding they uploaded or initiated, preventing conflicts of interest.
3. **Immutability of Audit Records:** No REST endpoint or application service shall expose `UPDATE` or `DELETE` operations on `audit_events` or `analysis_steps`.
4. **Deterministic Sovereignty:** If the LLM generates a finding claiming a numerical rule violation, the deterministic compliance engine must verify and validate that assertion against the raw extracted item before the finding can enter the database as a validated violation.
5. **No Blind Overwriting:** Rerunning an analysis on the same document creates a new `analysis_runs` record with a distinct UUID, preserving the historical provenance of prior runs.

---

## 4. Error Handling & Edge Case Requirements

1. **Scanned PDF (No Text):** Extracting text from a PDF containing solely raster images must return 0 characters and transition document status to `OCR_REQUIRED`. It must not invoke Gemini with empty strings.
2. **Corrupted File:** Upload of malformed PDF/DOCX headers must fail immediately in the upload pipeline with an explicit `INVALID_FILE_PAYLOAD` error.
3. **Gemini Outage / Rate Limit:** Network errors or HTTP 429 from Google Gen AI must be caught, retried up to 3 times with exponential backoff (1s, 2s, 4s + jitter). If exhausted, the analysis run status transitions to `FAILED` with a safe, sanitized error message.
4. **Missing Policy Sections:** If a policy document makes no mention of required receipts or invoices, the compliance engine must flag a finding of type `missing_requirement` with severity `HIGH` (not an explicit violation, since no violation occurred, but a missing mandatory governance clause).
5. **Contradictory Clauses:** If Section 3 allows ₹1,500 for meals but Section 7 caps meals at ₹1,000, the extraction schema captures both clauses, and the engine triggers an `inconsistency` finding for human review.
