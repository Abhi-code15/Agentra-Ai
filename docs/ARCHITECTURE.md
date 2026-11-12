# AGENTRA — System Architecture & Engineering Specification

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  
**Target:** Modular Monolith with Layered Clean Architecture  

---

## 1. Architecture Overview

Agentra is structured as a **Modular Monolith** engineered for high developer velocity, clear conceptual boundaries, strict transaction isolation, and uncompromising audibility. 

Rather than prematurely distributing business logic across microservices, the backend runs as a single, highly structured FastAPI process subdivided into distinct domain modules. Each module enforces strict layer separation:
1. **API / Presentation Layer:** Handles HTTP routing, input validation (Pydantic schemas), auth dependency injection, and uniform JSON serialization.
2. **Application / Service Layer:** Coordinates business workflows, use-case transactions, authorization enforcement, and orchestrates domain logic.
3. **Domain Layer:** Pure business entities, status state machines, deterministic compliance rule evaluators, and validation rules free of framework dependencies.
4. **Infrastructure Layer:** Concrete implementations of database persistence (SQLAlchemy 2.x repositories), file system storage, and the Gemini AI client.

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Layer"]
        WebUI["React 18 + Vite Web Application"]
    end

    subgraph APILayer ["FastAPI Presentation Layer (/api/v1)"]
        AuthRouter["auth.py (Authentication & Sessions)"]
        DocRouter["documents.py (Ingestion & Extraction)"]
        AnalysisRouter["analyses.py (Agent Orchestration)"]
        FindingRouter["findings.py (Finding Inquiries)"]
        ReviewRouter["reviews.py (HITL Governance Decisions)"]
        AuditRouter["audit.py (Immutable Audit Queries)"]
        HealthRouter["Health & Readiness Probes"]
        Middleware["Correlation ID & Security Middleware"]
    end

    subgraph ServiceLayer ["Application & Service Layer"]
        AuthService["AuthService (Tokens, Sessions, Hash)"]
        DocService["DocumentService (Mime, Storage, Text Extr)"]
        AgentOrchestrator["AgentOrchestrator (State & Loops)"]
        ComplianceService["ComplianceService (Rule Ingestion & Eval)"]
        ReviewService["ReviewService (HITL State Transitions)"]
        AuditService["AuditService (Immutable Event Logging)"]
    end

    subgraph DomainLayer ["Domain Layer"]
        RuleEngine["Deterministic Rule Engine"]
        FindingClassifier["Finding State Machine & Classifier"]
        ProvenanceTracker["Evidence Provenance Validator"]
    end

    subgraph InfraLayer ["Infrastructure & External Integrations"]
        GeminiAdapter["Google Gen AI Client Adapter (gemini-2.5-flash)"]
        FileStore["LocalStorage Manager (Private Directory)"]
        DocParsers["PyMuPDF (PDF) & python-docx (DOCX)"]
        SQLAlchemyRepos["SQLAlchemy 2.x Repositories"]
    end

    subgraph DataLayer ["Data Persistence"]
        PostgresDB[("PostgreSQL Database (UUIDs, FKs, JSONB)")]
        DiskStorage[("Encrypted Local File Storage")]
    end

    WebUI -->|HTTP / JSON + HttpOnly Cookies| Middleware
    Middleware --> APILayer
    APILayer --> ServiceLayer
    ServiceLayer --> DomainLayer
    ServiceLayer --> InfraLayer
    InfraLayer --> SQLAlchemyRepos
    SQLAlchemyRepos --> PostgresDB
    InfraLayer --> FileStore
    FileStore --> DiskStorage
    InfraLayer --> GeminiAdapter
    InfraLayer --> DocParsers
```

---

## 2. Component Responsibility Matrix

| Component | Layer | Primary Responsibility | Direct Dependencies |
| :--- | :--- | :--- | :--- |
| `API Routers` | Presentation | Validate HTTP input, extract JWT, call Service methods, format standard response | Services, Pydantic Schemas, Dependencies |
| `AuthService` | Application | Argon2id verification, JWT minting, refresh token rotation, session revocation | User Repo, Session Repo, Security utils |
| `DocumentService` | Application | Magic byte checks, file storage coordination, text extraction dispatch | Doc Repo, Extraction Repo, FileStore, Parsers |
| `AgentOrchestrator`| Application | Step-by-step agent loop, tool dispatch, state transitions, step logging | Tool Registry, Analysis Repo, Step Repo, Gemini |
| `ToolRegistry` | Application | Registry of 4 approved tools, argument validation, and invocation isolation | Service tools, Domain logic |
| `ComplianceEngine` | Domain | Mathematical & structural rule evaluation with allowlisted operators | Compliance Rules, Extracted Entities |
| `ReviewService` | Application | HITL decisions, reviewer authorization, atomic finding updates | Finding Repo, Review Task Repo, Audit Repo |
| `GeminiClient` | Infrastructure| Google Gen AI SDK wrapper, structured prompt rendering, retry logic | Google Gen AI SDK, Settings |
| `FileStorage` | Infrastructure| Private disk write/delete, SHA-256 calculation, path traversal guard | File system, Settings |
| `AuditService` | Infrastructure| Structured audit event creation with correlation ID | Audit Event Repo, Request Context |

---

## 3. Dependency Rules & Architecture Boundaries

1. **Inward-Facing Dependencies:** API routes depend on Services. Services depend on Repositories and Domain logic. Repositories depend on SQLAlchemy models.
2. **No Direct Route Queries:** API routes must NEVER execute direct SQL or SQLAlchemy session queries; all queries pass through typed repositories.
3. **No External Calls in Domain:** The `RuleEngine` is pure Python. It never calls the database, HTTP endpoints, or Gemini.
4. **No LLM in Transaction:** External network calls to Gemini must NEVER occur while holding an active PostgreSQL transaction lock. Transactions are opened to save status, closed during LLM inference, and opened again to record outputs.
5. **No Circular Imports:** Dependency injection via FastAPI `Depends()` enforces clean unidirectional graphs.

---

## 4. End-to-End Lifecycles

### 4.1 Document Ingestion & Processing Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Client)
    participant API as Documents API
    participant DocSvc as DocumentService
    participant Store as LocalFileStorage
    participant Extractor as PyMuPDF / python-docx
    participant DB as PostgreSQL

    User->>API: POST /api/v1/documents (multipart/form-data)
    API->>DocSvc: upload_document(file, current_user)
    DocSvc->>DocSvc: Validate file size (<= 25MB) & Magic Bytes
    DocSvc->>Store: save_file(stream, storage_key)
    Store-->>DocSvc: file_path, sha256_checksum
    DocSvc->>DB: INSERT into documents (status: UPLOADED)
    DB-->>DocSvc: document_id (UUID)
    
    DocSvc->>Extractor: extract_text(file_path, mime_type)
    alt Scanned PDF (0 chars extracted)
        Extractor-->>DocSvc: empty_text
        DocSvc->>DB: UPDATE documents (status: OCR_REQUIRED)
        DocSvc-->>API: DocumentResponse (status: OCR_REQUIRED)
    else Extractable Text Present
        Extractor-->>DocSvc: page_text_map, total_pages
        DocSvc->>DB: INSERT into document_extractions (status: COMPLETED)
        DocSvc->>DB: UPDATE documents (status: READY_FOR_ANALYSIS)
        DocSvc-->>API: DocumentResponse (status: READY_FOR_ANALYSIS)
    end
    API-->>User: 201 Created (document_id, status, metadata)
```

---

### 4.2 AI Agent Orchestration & Compliance Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Client)
    participant API as Analyses API
    participant Orch as AgentOrchestrator
    participant Tool as ToolExecutor
    participant Gemini as Google Gemini 2.5
    participant Rules as Deterministic Rule Engine
    participant DB as PostgreSQL

    User->>API: POST /api/v1/documents/{id}/analyze
    API->>Orch: start_analysis(document_id, user_id)
    Orch->>DB: INSERT analysis_runs (status: RUNNING)
    
    Note over Orch: Step 1: Extract Document Information
    Orch->>Tool: execute("extract_document_information", doc_id)
    Tool->>Gemini: generate_content(prompt, schema=ExtractionSchema)
    Gemini-->>Tool: Validated Structured JSON
    Tool-->>Orch: Extracted Entities (Approval Tiers, Limits, Quotes)
    Orch->>DB: INSERT analysis_steps (Step 1, Tool: extract, status: SUCCESS)
    Orch->>DB: INSERT extracted_items (...)

    Note over Orch: Step 2: Retrieve Relevant Evidence
    Orch->>Tool: execute("retrieve_document_evidence", query)
    Tool-->>Orch: Exact Page Passages & Quotes
    Orch->>DB: INSERT analysis_steps (Step 2, Tool: retrieve, status: SUCCESS)

    Note over Orch: Step 3: Evaluate Deterministic Rules
    Orch->>Tool: execute("evaluate_compliance_rules", extracted_data)
    Tool->>Rules: evaluate(extracted_tiers, enabled_rules)
    Rules-->>Tool: Rule Evaluation Results (PASS, FAIL, NEEDS_REVIEW)
    Tool-->>Orch: Findings List (violations, ambiguities, gaps)
    Orch->>DB: INSERT analysis_steps (Step 3, Tool: evaluate, status: SUCCESS)

    Note over Orch: Step 4: Persist Findings & Create Review Tasks
    Orch->>DB: INSERT findings (title, severity, evidence, status: PENDING_REVIEW)
    Orch->>DB: INSERT review_tasks (finding_id, status: OPEN)
    Orch->>DB: UPDATE analysis_runs (status: COMPLETED)
    Orch-->>API: AnalysisRunSummary
    API-->>User: 200 OK (analysis_run_id, findings_count, status)
```

---

### 4.3 Human-in-the-Loop Review Lifecycle

```mermaid
stateDiagram-v2
    [*] --> OPEN: Finding Created by Agent
    OPEN --> PENDING_REVIEW: Review Task Queued
    
    PENDING_REVIEW --> APPROVED: Reviewer Confirms Finding (with rationale)
    PENDING_REVIEW --> REJECTED: Reviewer Dismisses Finding (mandatory comment)
    PENDING_REVIEW --> NEEDS_REVISION: Reviewer Requests Further Investigation
    
    NEEDS_REVISION --> PENDING_REVIEW: Additional Evidence Submitted
    
    APPROVED --> [*]: Audit Event Logged & Archived
    REJECTED --> [*]: Audit Event Logged & Dismissed
```

---

## 5. Security & Isolation Boundaries

1. **User Identity Boundary:** Verified via Argon2id hash at login; signed JWT access token in authorization header (`Bearer <token>`).
2. **Session Persistence Boundary:** Rotating refresh token stored in an `HttpOnly`, `Secure`, `SameSite=Lax` cookie. Browser JavaScript cannot access or tamper with refresh tokens.
3. **Data Access Boundary:** Every repository query filters by `owner_id == current_user.id`, except for authorized `REVIEWER` roles inspecting assigned reviews.
4. **File System Boundary:** Uploaded documents are stored outside the public directory tree (`storage/documents/<uuid>.dat`). Filenames are strictly UUIDs; path traversal (`../`) is impossible.
5. **AI Safety Boundary:** Document contents are treated as untrusted user inputs wrapped in XML delimiters. System prompts strictly prohibit tool invocation or policy modification via document contents.
6. **Tool Execution Boundary:** The agent cannot execute arbitrary Python, system commands, or SQL. Only 4 pre-registered, strongly typed tools are callable.

---

## 6. Resilience & Failure Handling Strategy

```
+---------------------------+-----------------------------------+------------------------------------------+
|       Failure Mode        |         Detection Point           |           Mitigation / Recovery          |
+---------------------------+-----------------------------------+------------------------------------------+
| Network Timeout (Gemini)  | GeminiClient HTTP Call            | Exponential backoff retry (3x, 1s/2s/4s) |
| Schema Validation Error   | Pydantic Parse in GeminiParser    | Transition run to FAILED; log raw parse  |
| Database Connection Drop  | SQLAlchemy Session pool checkout  | Auto reconnect; fail request with 503    |
| File Parsing Crash (PDF)  | PyMuPDF Document open             | Catch MuPDF error; mark status CORRUPT   |
| Step Count Overflow       | AgentOrchestrator loop check      | Abort loop at step 6; flag STEP_LIMIT    |
| Invalid State Transition  | ReviewService.decide_review()     | 400 Bad Request; atomic rollback         |
+---------------------------+-----------------------------------+------------------------------------------+
```

---

## 7. Future Extension Points (Post-MVP)
- **OCR Pipeline:** Drop-in integration of Tesseract or Google Cloud Vision for scanned document image OCR.
- **Asynchronous Task Queue:** Transitioning `AgentOrchestrator` execution to Celery/ARQ with Redis for long documents ($\ge 200$ pages).
- **RAG Vector Search:** Adding pgvector extension to PostgreSQL for semantic clause retrieval across thousands of historical policies.
- **Enterprise SSO:** SAML 2.0 and OIDC integrations for Google Workspace and Microsoft 365 identity federation.
