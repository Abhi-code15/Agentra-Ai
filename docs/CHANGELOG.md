# AGENTRA — Changelog

All notable changes to the Agentra project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-12
### Added
- **Core Architecture & Foundation:**
  - Modular monolith architecture in FastAPI with PostgreSQL 15+ backend and React 18 frontend.
  - Correlation ID injection middleware (`X-Correlation-ID`) and structured JSON logging.
  - Alembic database migration baseline (`56643401829d`) configuring all 11 relational tables with UUID PKs, JSONB, and foreign key constraints.
  - Multi-stage Dockerfiles (`backend/Dockerfile`, `frontend/Dockerfile`) and `docker-compose.yml` for unified containerized deployment.
- **Authentication & Security:**
  - Argon2id password hashing and PyJWT access token generation.
  - HttpOnly rotating refresh token cookies with automatic family revocation upon replay attack detection.
  - Strict Broken Object-Level Authorization (BOLA) isolation across all document and analysis operations.
  - Role-Based Access Control (`USER`, `REVIEWER`, `ADMIN`).
- **Document Ingestion & Text Extraction:**
  - Secure private disk storage (`LocalStorageManager`) using random UUID keys and path traversal defense (`..` sanitization).
  - Magic byte file signature validation (blocking executables, scripts, and MIME spoofing).
  - PyMuPDF and python-docx text extraction engines with page-level metadata.
  - Scanned / empty PDF detection flagging `OCR_REQUIRED`.
- **Gemini AI Integration:**
  - Google Gemini 2.5 Flash SDK client adapter with structured Pydantic schema validation.
  - Prompt injection defense using `<untrusted_document_content>` delimiter isolation.
  - Substring quote provenance verifier ensuring extracted evidence matches original document text verbatim.
- **Compliance Engine & Controlled Agent Orchestrator:**
  - Pure Python deterministic rule engine (`equals`, `less_than_or_equal`, `greater_than`, `contains`, `exists`).
  - Pre-seeded corporate expense policy compliance rules (approval limits, receipt submission windows).
  - Bounded 4-step controlled agent orchestrator with hard circuit breaker at step 6.
  - Persistent step telemetry in `agent_execution_steps` capturing tool inputs, outputs, and execution timings.
- **Human Review (HITL) & Immutable Audit Ledger:**
  - Human review workflow with optimistic concurrency control (`status = 'OPEN'`).
  - Reviewer self-approval prohibition (`REVIEWER_SELF_APPROVAL_PROHIBITED`).
  - Mandatory justification comments for finding rejections and revision requests.
  - Append-only immutable `audit_events` ledger recording all auth, upload, analysis, and review lifecycle actions.
- **Modern Frontend Dashboard:**
  - React 18 + Vite + Tailwind CSS dashboard with responsive sidebar, stats overview, and role pill indicators.
  - Complete pages: Login, Register, Dashboard, Documents, Document Detail, Analysis Detail, Review Queue, and Audit Ledger.
  - Axios API client with automatic 401 refresh token retry interceptor.
- **Testing & Demonstration Dataset:**
  - 20-step master end-to-end acceptance test scenario (`tests/e2e/test_acceptance_scenario.py`).
  - Dedicated security boundary test suite (`tests/security/test_security_boundaries.py`).
  - 33 passing automated tests with 92% statement code coverage.
  - Official demonstration dataset generator (`demo/generate_demo_policy.py`) producing styled policy PDF (`demo/sample_expense_policy.pdf`).

## [0.1.0-milestone0] - 2026-11-12
### Added
- Comprehensive Product Requirements Document (`docs/PRD.md`) with target user personas and primary expense reimbursement business scenario.
- Engineering Requirements Specification (`docs/REQUIREMENTS.md`) defining functional matrix, P0 scope boundaries, and invariant business rules.
- Modular Monolith System Architecture (`docs/ARCHITECTURE.md`) with clean layering and end-to-end Mermaid sequence diagrams.
- PostgreSQL Entity Relationship Diagram (`docs/ERD.md`), Database Specification (`docs/DATABASE.md`), and Complete Data Dictionary (`docs/DATA_DICTIONARY.md`).
- Database Architectural Decisions (`docs/DB_DECISIONS.md`) justifying UUIDs, hybrid relational-JSONB modeling, and strict FK deletion rules.
- REST API v1 Specification (`docs/API.md`) and Comprehensive Machine Error Catalog (`docs/API_ERROR_CATALOG.md`).
- AI Integration Architecture (`docs/AI/AI_ARCHITECTURE.md`), Versioned Prompt Catalog (`docs/AI/PROMPT_CATALOG.md`), and Evaluation Benchmark Dataset (`docs/AI/MODEL_EVALUATION.md`).
- Controlled Agent Orchestrator Design (`docs/AGENT/AGENT_DESIGN.md`), Tool Registry (`docs/AGENT/TOOL_REGISTRY.md`), and Execution State Transitions (`docs/AGENT/EXECUTION_FLOW.md`).
- STRIDE Threat Model (`docs/SECURITY/THREAT_MODEL.md`) and Detailed Security Controls (`docs/SECURITY/SECURITY_CONTROLS.md`).
- Complete Testing Strategy (`docs/TESTING.md`) covering unit, integration, BOLA security suites, and the 20-step master acceptance scenario.
- Deployment Operations Guide (`docs/DEPLOYMENT.md`) and Structured Observability Specification (`docs/OBSERVABILITY.md`).
- Architecture Decision Records (`ADR-001` through `ADR-008`).
- Independent Principal Engineer Design Review (`docs/DESIGN_REVIEW.md`) auditing 15 architectural and security dimensions.
