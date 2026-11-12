# AGENTRA — Entity Relationship Diagram (ERD)

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  
**Target:** PostgreSQL 15+ Schema Specification  

---

## 1. High-Level Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ refresh_sessions : "maintains"
    users ||--o{ documents : "owns"
    users ||--o{ analysis_runs : "initiates"
    users ||--o{ review_tasks : "assigned to"
    users ||--o{ audit_events : "acts as"

    documents ||--o{ document_extractions : "has"
    documents ||--o{ analysis_runs : "analyzed in"

    analysis_runs ||--o{ analysis_steps : "executes"
    analysis_runs ||--o{ extracted_items : "produces"
    analysis_runs ||--o{ findings : "generates"

    compliance_rules ||--o{ findings : "evaluates against"

    findings ||--o{ review_tasks : "triggers"

    users {
        uuid id PK
        string email UK
        string full_name
        string password_hash
        string role
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    refresh_sessions {
        uuid id PK
        uuid user_id FK
        string token_hash UK
        timestamp expires_at
        timestamp revoked_at
        string user_agent
        string ip_address
        timestamp created_at
        timestamp last_used_at
    }

    documents {
        uuid id PK
        uuid owner_id FK
        string original_filename
        string storage_key UK
        string mime_type
        string file_extension
        bigint file_size_bytes
        string checksum_sha256
        string document_status
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    document_extractions {
        uuid id PK
        uuid document_id FK
        string extractor_name
        string extractor_version
        text extracted_text
        integer page_count
        string extraction_status
        jsonb metadata
        timestamp created_at
    }

    analysis_runs {
        uuid id PK
        uuid document_id FK
        uuid requested_by FK
        string status
        string provider
        string model_name
        string prompt_version
        timestamp started_at
        timestamp completed_at
        string error_code
        string safe_error_message
        jsonb execution_metadata
        timestamp created_at
    }

    analysis_steps {
        uuid id PK
        uuid analysis_run_id FK
        integer step_number
        string step_type
        string tool_name
        jsonb input_metadata
        jsonb output_metadata
        string status
        integer duration_ms
        string error_code
        timestamp started_at
        timestamp completed_at
    }

    extracted_items {
        uuid id PK
        uuid analysis_run_id FK
        string item_type
        string item_key
        jsonb extracted_value
        integer source_page
        text evidence_quote
        jsonb evidence_location
        string validation_status
        timestamp created_at
    }

    compliance_rules {
        uuid id PK
        string rule_code UK
        string name
        text description
        string category
        string severity
        jsonb rule_definition
        boolean is_enabled
        integer version
        timestamp created_at
        timestamp updated_at
    }

    findings {
        uuid id PK
        uuid analysis_run_id FK
        uuid rule_id FK
        string finding_code
        string title
        text description
        string severity
        string finding_type
        jsonb evidence
        string confidence_indicator
        string status
        timestamp created_at
        timestamp updated_at
    }

    review_tasks {
        uuid id PK
        uuid finding_id FK
        uuid assigned_reviewer_id FK
        string status
        string decision
        text reviewer_comments
        timestamp decided_at
        timestamp created_at
        timestamp updated_at
    }

    audit_events {
        uuid id PK
        uuid actor_id FK
        string event_type
        string entity_type
        uuid entity_id
        uuid request_id
        uuid analysis_run_id FK
        jsonb event_metadata
        timestamp created_at
    }
```

---

## 2. Cardinality and Referential Integrity Rules

1. **`users` $\to$ `refresh_sessions` (1:N):**
   - Cascade: `ON DELETE CASCADE`. If a user account is deleted, their active sessions are immediately erased.
2. **`users` $\to$ `documents` (1:N):**
   - Cascade: `ON DELETE RESTRICT`. A user account cannot be deleted if active corporate documents exist (requires explicit document transfer or purge).
3. **`documents` $\to$ `document_extractions` (1:N):**
   - Cascade: `ON DELETE CASCADE`. Removing a document purges its derived raw text cache.
4. **`documents` $\to$ `analysis_runs` (1:N):**
   - Cascade: `ON DELETE RESTRICT`. Preserves governance history even if a document is soft-deleted.
5. **`analysis_runs` $\to$ `analysis_steps` (1:N):**
   - Cascade: `ON DELETE CASCADE`. Execution telemetry belongs solely to its analysis run.
6. **`analysis_runs` $\to$ `extracted_items` (1:N):**
   - Cascade: `ON DELETE CASCADE`. Derived items bound to run lifecycle.
7. **`analysis_runs` $\to$ `findings` (1:N):**
   - Cascade: `ON DELETE RESTRICT`. Findings tied to compliance outcomes cannot be casually dropped.
8. **`compliance_rules` $\to$ `findings` (1:N):**
   - Foreign Key: `ON DELETE SET NULL`. If a historical rule definition is decommissioned, findings retain a snapshot of what was evaluated.
9. **`findings` $\to$ `review_tasks` (1:N):**
   - Cascade: `ON DELETE RESTRICT`. Review decisions are legal records; deleting a finding requires resolution of all review tasks.
10. **`users` $\to$ `audit_events` (1:N):**
    - Foreign Key: `ON DELETE SET NULL`. If an actor is purged, the audit record remains intact with `actor_id = NULL` and metadata preserving historical identity.
