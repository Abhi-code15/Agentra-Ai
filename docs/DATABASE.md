# AGENTRA — Database Architecture & Engineering Specification

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  
**Database Engine:** PostgreSQL 15+  
**ORM:** SQLAlchemy 2.0 (Strict 2.x Declarative Syntax with Typing)  
**Migration Tool:** Alembic  

---

## 1. Database Design Philosophy

1. **Strict Data Integrity:** Use database-level constraints (`CHECK`, `FOREIGN KEY`, `UNIQUE`, `NOT NULL`) rather than relying exclusively on application code.
2. **UUID Primary Keys:** All tables use UUIDv4 primary keys (`uuid_generate_v4()` or application-generated `uuid.uuid4()`). This prevents ID enumeration attacks, facilitates distributed ID generation, and eliminates sequence contention.
3. **UTC Timestamps:** All datetime columns are timezone-aware UTC timestamps (`TIMESTAMPTZ` / `DateTime(timezone=True)`).
4. **Normalized Core with Targeted JSONB:** Structured relational entities form the primary backbone. `JSONB` is reserved for flexible telemetry, audit metadata, and parsed conditions that change across rule revisions.
5. **Short-Lived Transactions:** Transactions must never span external network requests (such as Google Gemini inference).

---

## 2. Table Definitions & Constraints

### 2.1 `users`
Stores user identities, credentials, and global system roles.
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'USER',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT ck_users_role CHECK (role IN ('USER', 'REVIEWER', 'ADMIN'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### 2.2 `refresh_sessions`
Tracks active and revoked refresh tokens for session rotation.
```sql
CREATE TABLE refresh_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ NULL,
    replaced_by_session_id UUID NULL,
    user_agent VARCHAR(512) NULL,
    ip_address VARCHAR(45) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_refresh_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_refresh_sessions_replacement FOREIGN KEY (replaced_by_session_id) REFERENCES refresh_sessions(id) ON DELETE SET NULL,
    CONSTRAINT uq_refresh_sessions_token_hash UNIQUE (token_hash)
);

CREATE INDEX idx_refresh_sessions_user_id ON refresh_sessions(user_id);
CREATE INDEX idx_refresh_sessions_lookup ON refresh_sessions(token_hash) WHERE revoked_at IS NULL;
```

### 2.3 `documents`
Stores metadata and access state for uploaded policy documents.
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    storage_key VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_extension VARCHAR(10) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    document_status VARCHAR(50) NOT NULL DEFAULT 'UPLOADED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ NULL,
    CONSTRAINT fk_documents_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT uq_documents_storage_key UNIQUE (storage_key),
    CONSTRAINT ck_documents_status CHECK (document_status IN ('UPLOADED', 'PARSING', 'READY_FOR_ANALYSIS', 'OCR_REQUIRED', 'CORRUPT', 'FAILED', 'ARCHIVED'))
);

CREATE INDEX idx_documents_owner_created ON documents(owner_id, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_status ON documents(document_status);
```

### 2.4 `document_extractions`
Stores extracted page-by-page text caches and parsing metadata.
```sql
CREATE TABLE document_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    extractor_name VARCHAR(100) NOT NULL,
    extractor_version VARCHAR(50) NOT NULL,
    extracted_text TEXT NOT NULL,
    page_count INTEGER NOT NULL DEFAULT 1,
    extraction_status VARCHAR(50) NOT NULL DEFAULT 'COMPLETED',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_extractions_document FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT ck_extractions_status CHECK (extraction_status IN ('COMPLETED', 'FAILED', 'EMPTY'))
);

CREATE INDEX idx_extractions_document_id ON document_extractions(document_id);
```

### 2.5 `analysis_runs`
Represents an individual document compliance analysis run.
```sql
CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    requested_by UUID NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'INITIALIZED',
    provider VARCHAR(100) NOT NULL DEFAULT 'google_genai',
    model_name VARCHAR(100) NOT NULL DEFAULT 'gemini-2.5-flash',
    prompt_version VARCHAR(50) NOT NULL DEFAULT 'v1.0.0',
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ NULL,
    error_code VARCHAR(100) NULL,
    safe_error_message TEXT NULL,
    execution_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_analysis_runs_document FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE RESTRICT,
    CONSTRAINT fk_analysis_runs_user FOREIGN KEY (requested_by) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT ck_analysis_runs_status CHECK (status IN ('INITIALIZED', 'RUNNING', 'COMPLETED', 'FAILED', 'TIMED_OUT'))
);

CREATE INDEX idx_analysis_runs_document_created ON analysis_runs(document_id, created_at DESC);
CREATE INDEX idx_analysis_runs_requested_by ON analysis_runs(requested_by);
```

### 2.6 `analysis_steps`
Stores step-by-step telemetry, tool invocations, and timing for agent runs.
```sql
CREATE TABLE analysis_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL,
    step_number INTEGER NOT NULL,
    step_type VARCHAR(50) NOT NULL,
    tool_name VARCHAR(100) NULL,
    input_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    duration_ms INTEGER NOT NULL DEFAULT 0,
    error_code VARCHAR(100) NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ NULL,
    CONSTRAINT fk_analysis_steps_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
    CONSTRAINT uq_analysis_steps_run_step UNIQUE (analysis_run_id, step_number),
    CONSTRAINT ck_analysis_steps_status CHECK (status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED'))
);

CREATE INDEX idx_analysis_steps_run_step ON analysis_steps(analysis_run_id, step_number ASC);
```

### 2.7 `extracted_items`
Structured facts and parameters parsed by Gemini from policy text.
```sql
CREATE TABLE extracted_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL,
    item_type VARCHAR(100) NOT NULL,
    item_key VARCHAR(100) NOT NULL,
    extracted_value JSONB NOT NULL,
    source_page INTEGER NULL,
    evidence_quote TEXT NULL,
    evidence_location JSONB NOT NULL DEFAULT '{}'::jsonb,
    validation_status VARCHAR(50) NOT NULL DEFAULT 'VALIDATED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_extracted_items_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
    CONSTRAINT ck_extracted_items_status CHECK (validation_status IN ('VALIDATED', 'UNVALIDATED', 'MALFORMED'))
);

CREATE INDEX idx_extracted_items_run ON extracted_items(analysis_run_id);
CREATE INDEX idx_extracted_items_type ON extracted_items(item_type);
```

### 2.8 `compliance_rules`
Deterministic compliance rules configured in the platform.
```sql
CREATE TABLE compliance_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL DEFAULT 'EXPENSE_REIMBURSEMENT',
    severity VARCHAR(50) NOT NULL DEFAULT 'HIGH',
    rule_definition JSONB NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_compliance_rules_code UNIQUE (rule_code),
    CONSTRAINT ck_compliance_rules_severity CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
);

CREATE INDEX idx_compliance_rules_category ON compliance_rules(category) WHERE is_enabled IS TRUE;
```

### 2.9 `findings`
Identified policy violations, missing requirements, ambiguities, or inconsistencies.
```sql
CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL,
    rule_id UUID NULL,
    finding_code VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    finding_type VARCHAR(50) NOT NULL,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence_indicator VARCHAR(50) NOT NULL DEFAULT 'HIGH',
    status VARCHAR(50) NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_findings_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE RESTRICT,
    CONSTRAINT fk_findings_rule FOREIGN KEY (rule_id) REFERENCES compliance_rules(id) ON DELETE SET NULL,
    CONSTRAINT ck_findings_severity CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    CONSTRAINT ck_findings_type CHECK (finding_type IN ('violation', 'missing_requirement', 'ambiguity', 'inconsistency', 'manual_verification')),
    CONSTRAINT ck_findings_status CHECK (status IN ('OPEN', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'NEEDS_REVISION'))
);

CREATE INDEX idx_findings_run_id ON findings(analysis_run_id);
CREATE INDEX idx_findings_status_severity ON findings(status, severity);
```

### 2.10 `review_tasks`
Human-in-the-Loop review queue items.
```sql
CREATE TABLE review_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id UUID NOT NULL,
    assigned_reviewer_id UUID NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'OPEN',
    decision VARCHAR(50) NULL,
    reviewer_comments TEXT NULL,
    decided_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_review_tasks_finding FOREIGN KEY (finding_id) REFERENCES findings(id) ON DELETE RESTRICT,
    CONSTRAINT fk_review_tasks_reviewer FOREIGN KEY (assigned_reviewer_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_review_tasks_finding UNIQUE (finding_id),
    CONSTRAINT ck_review_tasks_status CHECK (status IN ('OPEN', 'IN_REVIEW', 'COMPLETED')),
    CONSTRAINT ck_review_tasks_decision CHECK (decision IS NULL OR decision IN ('APPROVED', 'REJECTED', 'NEEDS_REVISION'))
);

CREATE INDEX idx_review_tasks_status ON review_tasks(status);
CREATE INDEX idx_review_tasks_assigned_reviewer ON review_tasks(assigned_reviewer_id) WHERE status = 'OPEN';
```

### 2.11 `audit_events`
Append-only tamper-evident audit ledger.
```sql
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID NULL,
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    request_id UUID NOT NULL,
    analysis_run_id UUID NULL,
    event_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_events_actor FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_audit_events_run FOREIGN KEY (analysis_run_id) REFERENCES analysis_runs(id) ON DELETE SET NULL
);

CREATE INDEX idx_audit_events_created ON audit_events(created_at DESC);
CREATE INDEX idx_audit_events_entity ON audit_events(entity_type, entity_id);
CREATE INDEX idx_audit_events_request_id ON audit_events(request_id);
```

---

## 3. Transaction Boundary Rules & Concurrency

1. **Short-Lived Transactions:** A database transaction is held only for the duration of atomic DB operations (e.g., `INSERT analysis_runs`, then `COMMIT`).
2. **Never Hold Locks Across External API Calls:**
   - Step A: Transaction 1 creates `analysis_run` with status `RUNNING`, commits, and releases connection back to pool.
   - Step B: Agent calls Gemini API over HTTP (3-10s duration). No DB connection or transaction held.
   - Step C: Transaction 2 opens, writes `analysis_steps` and `extracted_items`, commits, and releases connection.
3. **Optimistic Locking for Reviews:** Review task decisions verify `status = 'OPEN'` at update time to prevent race conditions when two reviewers attempt concurrent adjudication:
   ```sql
   UPDATE review_tasks 
   SET status = 'COMPLETED', decision = :decision, reviewer_comments = :comments, decided_at = CURRENT_TIMESTAMP
   WHERE id = :task_id AND status = 'OPEN';
   ```
   If rows updated is 0, a concurrent update occurred, and the API returns a `409 Conflict`.

---

## 4. Alembic Migration Strategy

1. **Strict Version Control:** All DDL changes must be generated via Alembic (`alembic revision --autogenerate -m "..."`).
2. **Manual Review:** Every autogenerated migration file must be inspected before commit. Autogenerate often misses CHECK constraints or specific partial indexes.
3. **No In-Place Edits:** Once an Alembic migration is merged or deployed, it is immutable. Schema updates require a new forward migration.
4. **Offline DDL Safety:** Migration scripts must avoid long table locks on high-write tables (e.g. create indexes concurrently where needed in production).
