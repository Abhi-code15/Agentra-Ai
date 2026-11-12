# Agentra — Enterprise AI Governance and Document Intelligence Platform

> **"Intelligent Document Analysis. Transparent Decisions. Human-Controlled Governance."**

---

## 1. Executive Overview

Agentra is an enterprise-grade AI governance platform engineered to ingest corporate policy documents, extract structured operational parameters using Large Language Models (Google Gemini), evaluate those parameters against **deterministic Python compliance rules**, present evidence-backed findings, and facilitate Human-in-the-Loop (HITL) review.

Agentra enforces a strict architectural boundary between LLM interpretation and deterministic rule evaluation: **LLMs interpret natural language; Python code enforces compliance rules.**

---

## 2. Key Architecture Principles

1. **Modular Monolith:** Single FastAPI backend organized into clean layered modules (API $\to$ Service $\to$ Domain $\to$ Infrastructure) without microservices overhead.
2. **PostgreSQL as Sole Datastore:** Relational integrity, foreign keys, UUID primary keys, and JSONB payloads in PostgreSQL 15+.
3. **Controlled Agent Orchestrator:** Bounded 4-step execution flow with a strict circuit breaker (max 6 steps) preventing infinite loops.
4. **Deterministic Compliance Engine:** Python-based rule evaluator running hard mathematical, structural, and existence checks.
5. **Secure Authentication:** Argon2id password hashing, short-lived JWT access tokens in client memory, and rotating HttpOnly, Secure refresh cookies.
6. **Immutable Audit Ledger:** Tamper-evident audit logging of all authentication events, uploads, rule evaluations, and human decisions.

---

## 3. Technology Stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL 15+.
- **Document Processing:** PyMuPDF (PDF page-by-page text extraction), python-docx (DOCX paragraph & table parsing).
- **AI Integration:** Google Gen AI SDK (`gemini-2.5-flash`), Structured JSON schema outputs, XML prompt boundary delimiters.
- **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons, React Router v6.
- **Testing:** pytest, pytest-asyncio, httpx, TestClient.

---

## 4. Documentation Index

The complete engineering design is documented under `docs/`:

- [PRD.md](file:///docs/PRD.md): Product Requirements Document
- [REQUIREMENTS.md](file:///docs/REQUIREMENTS.md): Functional and Non-Functional Requirements
- [ARCHITECTURE.md](file:///docs/ARCHITECTURE.md): System Architecture & Sequence Lifecycles
- [DATABASE.md](file:///docs/DATABASE.md): PostgreSQL Schema, Indexes, & Transactions
- [ERD.md](file:///docs/ERD.md): Entity Relationship Diagram
- [DATA_DICTIONARY.md](file:///docs/DATA_DICTIONARY.md): Comprehensive Column Data Dictionary
- [API.md](file:///docs/API.md): REST API v1 Specification
- [API_ERROR_CATALOG.md](file:///docs/API_ERROR_CATALOG.md): Machine Error Codes & Responses
- [SECURITY_CONTROLS.md](file:///docs/SECURITY/SECURITY_CONTROLS.md): Authentication & Threat Defense
- [DESIGN_REVIEW.md](file:///docs/DESIGN_REVIEW.md): Independent Principal Engineer 15-Point Review
- [ADR Index](file:///docs/ADR/): Architecture Decision Records (ADR-001 through ADR-008)

---

## 5. Quickstart (Windows PowerShell)

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL 15+ (Running locally or via Docker)

### Backend Setup
```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env with your GEMINI_API_KEY and DATABASE_URL
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```

Visit the application at `http://localhost:5173`. API documentation is available at `http://localhost:8000/docs`.
