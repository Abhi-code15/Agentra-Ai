# AGENTRA — Comprehensive Data Dictionary

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  
**Target:** PostgreSQL 15+  

---

## 1. Entity: `users`
Represents registered user accounts, credentials, and access roles.

| Column | Data Type | Nullable | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | `gen_random_uuid()` | PK | Unique identifier for user |
| `email` | VARCHAR(255) | NO | None | UNIQUE, Normalized lowercase | User's primary login email address |
| `full_name` | VARCHAR(255) | NO | None | None | User's full display name |
| `password_hash` | VARCHAR(255) | NO | None | Argon2id format string | Cryptographically hashed password |
| `role` | VARCHAR(50) | NO | `'USER'` | CHECK IN (`'USER'`, `'REVIEWER'`, `'ADMIN'`) | Authorization role |
| `is_active` | BOOLEAN | NO | `TRUE` | None | Account activity toggle |
| `created_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Account creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Last profile update timestamp |

---

## 2. Entity: `refresh_sessions`
Maintains cryptographic session tokens for refresh token rotation.

| Column | Data Type | Nullable | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | `gen_random_uuid()` | PK | Unique session identifier |
| `user_id` | UUID | NO | None | FK $\to$ `users.id` (CASCADE) | User owning this session |
| `token_hash` | VARCHAR(255) | NO | None | UNIQUE | SHA-256 hash of refresh token |
| `expires_at` | TIMESTAMPTZ | NO | None | None | Absolute session expiration time |
| `revoked_at` | TIMESTAMPTZ | YES | NULL | None | Revocation timestamp if logged out |
| `replaced_by_session_id` | UUID | YES | NULL | FK $\to$ `refresh_sessions.id` (SET NULL) | Rotation chain pointer |
| `user_agent` | VARCHAR(512) | YES | NULL | None | Client browser User-Agent string |
| `ip_address` | VARCHAR(45) | YES | NULL | None | Client IP address for fraud detection |
| `created_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Session initiation timestamp |
| `last_used_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Timestamp of last access token refresh |

---

## 3. Entity: `documents`
Stores metadata and physical storage pointers for uploaded documents.

| Column | Data Type | Nullable | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | `gen_random_uuid()` | PK | Document primary key |
| `owner_id` | UUID | NO | None | FK $\to$ `users.id` (RESTRICT) | User who uploaded the document |
| `original_filename` | VARCHAR(255) | NO | None | None | Original client-side filename |
| `storage_key` | VARCHAR(255) | NO | None | UNIQUE | Server-side random UUID storage path |
| `mime_type` | VARCHAR(100) | NO | None | None | MIME type (`application/pdf`, etc.) |
| `file_extension` | VARCHAR(10) | NO | None | None | Extension (`.pdf`, `.docx`) |
| `file_size_bytes` | BIGINT | NO | None | $> 0$ | File size in bytes (max 25MB) |
| `checksum_sha256` | VARCHAR(64) | NO | None | Length = 64 hex chars | SHA-256 integrity hash |
| `document_status` | VARCHAR(50) | NO | `'UPLOADED'` | CHECK IN (`'UPLOADED'`, `'PARSING'`, `'READY_FOR_ANALYSIS'`, `'OCR_REQUIRED'`, `'CORRUPT'`, `'FAILED'`, `'ARCHIVED'`) | Lifecycle status |
| `created_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Upload timestamp |
| `updated_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Metadata update timestamp |
| `deleted_at` | TIMESTAMPTZ | YES | NULL | None | Soft delete timestamp |

---

## 4. Entity: `document_extractions`
Raw text and page-by-page mapping extracted from uploaded files.

| Column | Data Type | Nullable | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | `gen_random_uuid()` | PK | Extraction primary key |
| `document_id` | UUID | NO | None | FK $\to$ `documents.id` (CASCADE) | Associated document |
| `extractor_name` | VARCHAR(100) | NO | None | None | Engine used (`PyMuPDF`, `python-docx`) |
| `extractor_version`| VARCHAR(50) | NO | None | None | Version of extraction library |
| `extracted_text` | TEXT | NO | None | None | Full concatenated normalized text |
| `page_count` | INTEGER | NO | 1 | $> 0$ | Total pages parsed |
| `extraction_status`| VARCHAR(50) | NO | `'COMPLETED'` | CHECK IN (`'COMPLETED'`, `'FAILED'`, `'EMPTY'`) | Processing outcome |
| `metadata` | JSONB | NO | `'{}'::jsonb` | Valid JSON | Detailed page offsets & bounding boxes |
| `created_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Extraction timestamp |

---

## 5. Entity: `analysis_runs`
Tracks executions of the agent and compliance workflow on a document.

| Column | Data Type | Nullable | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | `gen_random_uuid()` | PK | Analysis run identifier |
| `document_id` | UUID | NO | None | FK $\to$ `documents.id` (RESTRICT) | Target document |
| `requested_by` | UUID | NO | None | FK $\to$ `users.id` (RESTRICT) | Initiating user |
| `status` | VARCHAR(50) | NO | `'INITIALIZED'` | CHECK IN (`'INITIALIZED'`, `'RUNNING'`, `'COMPLETED'`, `'FAILED'`, `'TIMED_OUT'`) | Workflow status |
| `provider` | VARCHAR(100) | NO | `'google_genai'` | None | AI provider identifier |
| `model_name` | VARCHAR(100) | NO | `'gemini-2.5-flash'` | None | Model identifier used |
| `prompt_version` | VARCHAR(50) | NO | `'v1.0.0'` | None | Version identifier of system prompt |
| `started_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Execution start timestamp |
| `completed_at` | TIMESTAMPTZ | YES | NULL | None | Execution finish timestamp |
| `error_code` | VARCHAR(100) | YES | NULL | None | Machine error code if failed |
| `safe_error_message`| TEXT | YES | NULL | None | Client-safe error message |
| `execution_metadata`| JSONB | NO | `'{}'::jsonb` | Valid JSON | Token usage, latency breakdown |
| `created_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Record creation timestamp |

---

## 6. Entity: `analysis_steps`
Records discrete execution steps taken by the Agent Orchestrator.

| Column | Data Type | Nullable | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | `gen_random_uuid()` | PK | Step primary key |
| `analysis_run_id` | UUID | NO | None | FK $\to$ `analysis_runs.id` (CASCADE) | Associated analysis run |
| `step_number` | INTEGER | NO | None | Unique per run ($1 \dots 6$) | Sequence order of execution step |
| `step_type` | VARCHAR(50) | NO | None | None | Type (`TOOL_EXECUTION`, `VALIDATION`) |
| `tool_name` | VARCHAR(100) | YES | NULL | None | Tool invoked if tool step |
| `input_metadata` | JSONB | NO | `'{}'::jsonb` | Valid JSON | Sanitized input parameters |
| `output_metadata`| JSONB | NO | `'{}'::jsonb` | Valid JSON | Sanitized execution observation |
| `status` | VARCHAR(50) | NO | `'PENDING'` | CHECK IN (`'PENDING'`, `'RUNNING'`, `'SUCCESS'`, `'FAILED'`, `'SKIPPED'`) | Step status |
| `duration_ms` | INTEGER | NO | 0 | $\ge 0$ | Step duration in milliseconds |
| `error_code` | VARCHAR(100) | YES | NULL | None | Step error code if failed |
| `started_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Step start timestamp |
| `completed_at` | TIMESTAMPTZ | YES | NULL | None | Step completion timestamp |

---

## 7. Entity: `extracted_items`
Structured entities extracted from the policy text.

| Column | Data Type | Nullable | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | `gen_random_uuid()` | PK | Extracted item identifier |
| `analysis_run_id` | UUID | NO | None | FK $\to$ `analysis_runs.id` (CASCADE) | Associated analysis run |
| `item_type` | VARCHAR(100) | NO | None | None | E.g. `APPROVAL_TIER`, `RECEIPT_REQUIREMENT` |
| `item_key` | VARCHAR(100) | NO | None | None | Lookup key |
| `extracted_value`| JSONB | NO | None | Valid JSON | Parsed typed value (Pydantic schema) |
| `source_page` | INTEGER | YES | NULL | $> 0$ | Source page in original document |
| `evidence_quote` | TEXT | YES | NULL | None | Verbatim quotation from document |
| `evidence_location`| JSONB | NO | `'{}'::jsonb` | Valid JSON | Bounding box, line numbers |
| `validation_status`| VARCHAR(50) | NO | `'VALIDATED'` | CHECK IN (`'VALIDATED'`, `'UNVALIDATED'`, `'MALFORMED'`) | Validation outcome |
| `created_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Timestamp created |

---

## 8. Entity: `compliance_rules`
Deterministic compliance checks against extracted items.

| Column | Data Type | Nullable | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | `gen_random_uuid()` | PK | Rule identifier |
| `rule_code` | VARCHAR(100) | NO | None | UNIQUE | E.g. `EXP_RULE_MANAGER_LIMIT` |
| `name` | VARCHAR(255) | NO | None | None | Human-readable rule title |
| `description` | TEXT | NO | None | None | Detailed governance description |
| `category` | VARCHAR(100) | NO | `'EXPENSE_REIMBURSEMENT'` | None | Rule grouping |
| `severity` | VARCHAR(50) | NO | `'HIGH'` | CHECK IN (`'LOW'`, `'MEDIUM'`, `'HIGH'`, `'CRITICAL'`) | Default issue severity |
| `rule_definition` | JSONB | NO | None | Valid JSON | Safe condition expression tree |
| `is_enabled` | BOOLEAN | NO | `TRUE` | None | Rule activation flag |
| `version` | INTEGER | NO | 1 | $\ge 1$ | Rule definition revision |
| `created_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Created timestamp |
| `updated_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Last modified timestamp |

---

## 9. Entity: `findings`
Identified issues and compliance evaluation results.

| Column | Data Type | Nullable | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | `gen_random_uuid()` | PK | Finding identifier |
| `analysis_run_id` | UUID | NO | None | FK $\to$ `analysis_runs.id` (RESTRICT) | Originating analysis run |
| `rule_id` | UUID | YES | NULL | FK $\to$ `compliance_rules.id` (SET NULL) | Associated rule if deterministic |
| `finding_code` | VARCHAR(100) | NO | None | None | Machine finding code |
| `title` | VARCHAR(255) | NO | None | None | Summary title |
| `description` | TEXT | NO | None | None | Full explanation of finding |
| `severity` | VARCHAR(50) | NO | None | CHECK IN (`'LOW'`, `'MEDIUM'`, `'HIGH'`, `'CRITICAL'`) | Severity level |
| `finding_type` | VARCHAR(50) | NO | None | CHECK IN (`'violation'`, `'missing_requirement'`, `'ambiguity'`, `'inconsistency'`, `'manual_verification'`) | Taxonomy category |
| `evidence` | JSONB | NO | `'{}'::jsonb` | Valid JSON | Quotes, page refs, extracted values |
| `confidence_indicator`| VARCHAR(50) | NO | `'HIGH'` | None | Confidence rating |
| `status` | VARCHAR(50) | NO | `'OPEN'` | CHECK IN (`'OPEN'`, `'PENDING_REVIEW'`, `'APPROVED'`, `'REJECTED'`, `'NEEDS_REVISION'`) | Finding workflow state |
| `created_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Created timestamp |
| `updated_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Last updated timestamp |

---

## 10. Entity: `review_tasks`
Tasks queued for human governance review.

| Column | Data Type | Nullable | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | `gen_random_uuid()` | PK | Review task identifier |
| `finding_id` | UUID | NO | None | FK $\to$ `findings.id` (RESTRICT), UNIQUE | 1:1 mapping with finding |
| `assigned_reviewer_id`| UUID | YES | NULL | FK $\to$ `users.id` (SET NULL) | Reviewer assigned |
| `status` | VARCHAR(50) | NO | `'OPEN'` | CHECK IN (`'OPEN'`, `'IN_REVIEW'`, `'COMPLETED'`) | Task workflow state |
| `decision` | VARCHAR(50) | YES | NULL | CHECK IN (`'APPROVED'`, `'REJECTED'`, `'NEEDS_REVISION'`) | Review decision |
| `reviewer_comments`| TEXT | YES | NULL | Mandatory if decision is REJECTED | Reviewer commentary |
| `decided_at` | TIMESTAMPTZ | YES | NULL | None | Adjudication timestamp |
| `created_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Task creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Task update timestamp |

---

## 11. Entity: `audit_events`
Immutable ledger of all security, governance, and business transactions.

| Column | Data Type | Nullable | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | NO | `gen_random_uuid()` | PK | Audit record identifier |
| `actor_id` | UUID | YES | NULL | FK $\to$ `users.id` (SET NULL) | User responsible (NULL if system) |
| `event_type` | VARCHAR(100) | NO | None | None | E.g. `AUTH_LOGIN`, `REVIEW_APPROVED` |
| `entity_type` | VARCHAR(100) | NO | None | None | Target entity (`document`, `review`, etc.) |
| `entity_id` | UUID | NO | None | None | Identifier of affected entity |
| `request_id` | UUID | NO | None | None | Correlation ID from HTTP request |
| `analysis_run_id` | UUID | YES | NULL | FK $\to$ `analysis_runs.id` (SET NULL) | Associated run if AI related |
| `event_metadata` | JSONB | NO | `'{}'::jsonb` | Valid JSON | Context (IP, old/new states, comments) |
| `created_at` | TIMESTAMPTZ | NO | `CURRENT_TIMESTAMP` | None | Immutable record timestamp |
