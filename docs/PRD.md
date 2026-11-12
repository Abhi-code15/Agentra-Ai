# AGENTRA — Product Requirements Document (PRD)

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  
**Author:** Principal System Architect & Product Engineering Team  
**Scope:** MVP Milestone 0 Design  

---

## 1. Product Overview

### 1.1 Product Identity
- **Product Name:** Agentra
- **Tagline:** *"Intelligent Document Analysis. Transparent Decisions. Human-Controlled Governance."*
- **Category:** Enterprise AI Governance and Document Intelligence Platform.

### 1.2 Executive Summary
Agentra is an enterprise-grade AI governance platform engineered to ingest, extract, analyze, and verify corporate policy documents against deterministic business compliance rules. By bridging state-of-the-art Large Language Model (LLM) document parsing (via Google Gemini) with deterministic rule engines and an auditable Human-in-the-Loop (HITL) review workflow, Agentra eliminates manual compliance review bottlenecks while upholding enterprise security, strict audit provenance, and zero unvalidated autonomous decisions.

---

## 2. Problem Statement & Market Context

### 2.1 The Problem
Enterprises manage hundreds of sprawling operational policies, reimbursement limits, vendor agreements, and compliance manuals. Manual document review suffers from severe operational deficits:
1. **High Latency & Cognitive Fatigue:** Manual verification takes hours per document, leading to oversights.
2. **Inconsistent Information Extraction:** Different human reviewers extract varying clauses and numbers from identical texts.
3. **Ambiguity and Contradiction Overlook:** Revisions across fiscal years cause internal contradictions (e.g., conflicting travel meal caps) that manual checks rarely reconcile.
4. **Black-box AI Distrust:** Enterprises cannot rely on purely generative "chatbots" that produce hallucinations, lack quote-level citations, or make unchecked decisions.
5. **Absence of Audit Provenance:** Regulatory and audit bodies require a verifiable link between a policy clause, a deterministic rule check, and a named human reviewer's signed approval.

### 2.2 The Solution
Agentra solves this with a **tripartite verification architecture**:
1. **Document Intelligence Layer:** High-fidelity document parsing (PDF and DOCX) extracting raw text while tracking page numbers and offsets.
2. **Deterministic Compliance Engine:** Python-based rule evaluator running hard mathematical, structural, and existence checks on extracted entities (never delegating legal/rule math to the LLM).
3. **HITL Review & Audit Pipeline:** Findings are classified with exact evidence quotes and routed to human reviewers for formal approval, rejection, or amendment, recorded in an append-only audit trail.

---

## 3. Target Users & Personas

### 3.1 Persona 1: Operational Submitter (`USER`)
- **Role:** Department Manager, Policy Author, or Operations Associate.
- **Goals:** Upload newly drafted or revised policy documents (e.g., *Expense Reimbursement Policy 2026*); run compliance analysis to detect contradictions, missing clauses, or policy gaps before deployment.
- **Key Actions:** 
  - Register and authenticate.
  - Upload PDF/DOCX policy documents.
  - Trigger automated compliance analyses.
  - View analysis dashboards, extraction summaries, and rule evaluations.
  - Track findings lifecycle and view final resolution comments.
- **Constraints:** Cannot review or approve their own findings; cannot view documents owned by other users.

### 3.2 Persona 2: Compliance Officer / Governance Auditor (`REVIEWER`)
- **Role:** Enterprise Compliance Officer, Senior Legal Counsel, or Internal Auditor.
- **Goals:** Inspect system-generated findings, verify raw text evidence against corporate governance standards, and render legally binding review decisions.
- **Key Actions:**
  - View assigned review queue and prioritize by severity (CRITICAL, HIGH, MEDIUM, LOW).
  - Inspect highlighted evidence citations mapped directly back to source document pages.
  - Approve findings, reject false positives with rationale, or request further investigation.
  - Audit historical review decisions and export compliance logs.
- **Constraints:** All decisions require cryptographic actor attribution and mandatory commentary for rejections/amendments.

---

## 4. Primary Business Scenario: Expense Reimbursement Policy

To anchor the MVP with an exhaustive benchmark, the system targets corporate **Employee Expense Reimbursement Policies**:
- **Baseline Rule A (Approval Tiers):**
  - Expenses $\le$ ₹5,000 require Department Manager approval.
  - Expenses between ₹5,001 and ₹10,000 require Finance Approval.
  - Expenses $>$ ₹10,000 require Senior Management (VP/Director) approval.
- **Baseline Rule B (Documentation):**
  - Every claim must possess a valid itemized receipt/tax invoice within 30 days of spend.
- **Baseline Rule C (Exclusions & Caps):**
  - Alcohol without client entertainment pre-clearance is non-reimbursable.
  - Daily domestic per-diem meals cannot exceed ₹1,500.

**Agentra evaluates whether the uploaded policy document:**
1. Properly defines all tiered thresholds without arithmetic or managerial gaps.
2. Explicitly stipulates receipt requirements and submission deadlines.
3. Contains ambiguities (e.g., "reasonable expenses will be reimbursed" without currency limits).
4. Contains internal contradictions (e.g., Section 2 stating ₹5,000 limit, while Annexure A cites ₹3,000).

---

## 5. Scope Boundaries

```
+-------------------------------------------------------+------------------------------------------------------+
|                     IN SCOPE (P0)                     |                  EXCLUDED FROM MVP                   |
+-------------------------------------------------------+------------------------------------------------------+
| - Argon2id JWT Auth + HttpOnly Refresh Sessions       | - Autonomous multi-agent emergent communications     |
| - Secure PDF (PyMuPDF) and DOCX (python-docx) parsing | - Complex Vector Databases / Vector Embeddings (RAG) |
| - Gemini 2.5/Flash Structured Output Parsing          | - LangChain / LangGraph heavyweight frameworks       |
| - Controlled 4-step Agent Orchestrator with limits    | - Google Workspace / Microsoft 365 Direct Integrations|
| - Deterministic Python Rule Evaluation Engine         | - Scanned image OCR (Tesseract / Cloud Vision)       |
| - Human Review Queue with state-machine governance    | - Distributed microservices / Kubernetes / Kafka     |
| - Append-only Structured Audit & Observability Trails | - Dynamic multi-tenant organization hierarchies      |
| - Modern React (Vite + Tailwind CSS) Dashboard        | - Model drift monitoring & automated retraining      |
+-------------------------------------------------------+------------------------------------------------------+
```

---

## 6. User Stories & Acceptance Criteria

### US-1: Document Ingestion & Storage
- **As a** `USER`,
- **I want to** upload a PDF or DOCX policy file up to 25 MB,
- **So that** it is safely stored and queued for structural text extraction.
- **Acceptance Criteria:**
  - File format checked via magic bytes (`%PDF-` / PK zip signature), not mere extension.
  - Server assigns a cryptographically random UUID storage key; original filename never used on disk.
  - File stored in private storage root outside public web server directories.
  - Computes and stores SHA-256 checksum to prevent undetected file tampering.

### US-2: Document Extraction Provenance
- **As a** `USER` or `REVIEWER`,
- **I want to** inspect extracted paragraphs tagged with accurate page numbers,
- **So that** any subsequent rule finding links directly to undeniable source text.
- **Acceptance Criteria:**
  - Text extracted page-by-page using PyMuPDF (PDF) or python-docx paragraph/table walker.
  - Scanned PDFs with no extractable text immediately fail fast with status `OCR_REQUIRED`.
  - Empty or unreadable files fail gracefully with explicit user-facing error messages.

### US-3: Controlled Agentic Document Analysis
- **As a** `USER`,
- **I want to** execute analysis on an uploaded document,
- **So that** key governance thresholds, approval tiers, and documentation rules are extracted.
- **Acceptance Criteria:**
  - Gemini invoked using strict Pydantic schemas (Structured Outputs).
  - Prompts clearly separate system governance instructions from untrusted document input.
  - Agent state tracks execution steps, tool invocations, and timing metrics in `analysis_steps`.
  - Hard step counter limit (maximum 6 steps) prevents infinite execution loops.

### US-4: Deterministic Compliance Verification
- **As an** Enterprise Auditor,
- **I want** corporate rules evaluated by a deterministic Python engine rather than an LLM prompt,
- **So that** mathematical and threshold checks are guaranteed 100% reproducible.
- **Acceptance Criteria:**
  - Compliance engine compares extracted values against configured rules using safe operators (`equals`, `less_than_or_equal`, `greater_than`, `contains`, `exists`).
  - Rule evaluation produces four explicit states: `PASS`, `FAIL`, `INSUFFICIENT_DATA`, `NEEDS_REVIEW`.
  - Each finding records exact `evidence_quote` and `source_page`.

### US-5: Human-in-the-Loop Governance
- **As a** `REVIEWER`,
- **I want to** review flagged findings, read the original text citation, and submit an authoritative verdict,
- **So that** false positives are filtered and actual violations are formally recorded.
- **Acceptance Criteria:**
  - Review queue displays findings filtered by status (`PENDING_REVIEW`, `APPROVED`, `REJECTED`, `NEEDS_REVISION`).
  - Reviewer decisions require transactional status update, reviewer ID recording, and timestamping.
  - Rejections strictly require reviewer comments.
  - Append-only audit record created on every review action.

---

## 7. Non-Functional Requirements (NFRs)

### 7.1 Security & Privacy
- **NFR-SEC-1:** Zero exposure of secrets; API keys, JWT secrets, and database credentials only via environment variables.
- **NFR-SEC-2:** Passwords hashed using Argon2id with memory cost 64 MB, 3 iterations, 4 parallelism lanes.
- **NFR-SEC-3:** Authentication via short-lived JWT access tokens (15 mins) and rotating HttpOnly, Secure, SameSite refresh cookies (7 days).
- **NFR-SEC-4:** Object-level authorization (IDOR protection) verified on every document, analysis, finding, and review query.
- **NFR-SEC-5:** Prompt injection defense: document text wrapped in XML boundaries (`<untrusted_document_content>`) with strict negative constraints.

### 7.2 Performance & Scalability
- **NFR-PERF-1:** Document text extraction completed within $\le 3.0$ seconds for documents up to 50 pages.
- **NFR-PERF-2:** Agent orchestration and rule execution completed within $\le 15.0$ seconds (excluding Gemini network latency).
- **NFR-PERF-3:** Database operations strictly scoped to short-lived sessions; transactions never held open across external LLM network requests.

### 7.3 Reliability & Resilience
- **NFR-REL-1:** Bounded exponential backoff with jitter on Gemini API timeouts (max 3 retries).
- **NFR-REL-2:** 100% atomic database operations with automatic rollback on exception.
- **NFR-REL-3:** Graceful degradation on model schema validation failure without persisting corrupted findings.

### 7.4 Maintainability & Code Quality
- **NFR-MAINT-1:** Strict PEP 8 adherence, 100% type hinting in Python backend.
- **NFR-MAINT-2:** Layered architecture: API $\to$ Service $\to$ Domain $\to$ Repository $\to$ Infrastructure.
- **NFR-MAINT-3:** Comprehensive automated test coverage (Unit, Integration, Security, Mocked AI).

---

## 8. Success Metrics & KPIs
1. **Extraction Accuracy:** $\ge 95\%$ recall on key policy parameters (monetary limits, approval authorities) on test benchmarks.
2. **Deterministic Reproducibility:** $100\%$ consistency in compliance rule evaluations given identical extracted inputs.
3. **Audit Completeness:** $100\%$ of review decisions, status transitions, and tool executions captured in immutable audit logs.
4. **Security Zero-Tolerance:** 0 vulnerabilities in broken object-level authorization (BOLA) and 0 unhandled prompt injection leaks during penetration testing.
