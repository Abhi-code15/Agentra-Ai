# AGENTRA — Comprehensive Testing Strategy

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  
**Test Framework:** pytest, pytest-asyncio, httpx  

---

## 1. Testing Pyramid & Principles

```
                  / \
                 / E2E \       (End-to-End Workflow & Governance Tests)
                /-------\
               / Security\     (BOLA, Token Replay, Injection, Traversal)
              /-----------\
             / Integration \   (FastAPI TestClient, SQLite/Postgres in-memory)
            /---------------\
           /   Unit Tests    \ (Rules, Parsers, Auth, State Machine, Mocks)
          /-------------------\
```

### Core Principles
1. **Zero External Flakiness in CI:** Tests must NEVER make live external calls to the Gemini API during automated unit/integration test runs. All LLM calls are mocked with deterministic fixtures.
2. **Transaction Isolation:** Each database integration test executes in a clean transaction that rolls back on test teardown.
3. **Assert Both Sides:** Every feature requires tests for both the happy path (2xx) and explicit failure modes (4xx/5xx).

---

## 2. Unit Testing Strategy

- **Directory:** `tests/unit/`
- **Target Coverage:** $\ge 85\%$ line coverage across domain and utility modules.
- **Key Test Suites:**
  - `test_security.py`: Argon2id password hashing, verification, JWT creation, claims validation, refresh token hash generation.
  - `test_rule_engine.py`: Deterministic rule evaluator testing all operators (`equals`, `less_than_or_equal`, `greater_than`, `contains`, `exists`) against valid and invalid edge cases.
  - `test_parsers.py`: PyMuPDF and python-docx text extraction functions, handling corrupt files and empty documents.
  - `test_agent_state.py`: `AgentState` transitions, step counter incrementation, step limit circuit breaker tripping at step 6.
  - `test_tool_validation.py`: Pydantic input/output validation for all 4 registered tools.

---

## 3. Integration Testing Strategy

- **Directory:** `tests/integration/`
- **Target Components:** API routers, service layers, and database interactions using `httpx.AsyncClient` or FastAPI `TestClient`.
- **Key Test Suites:**
  - `test_auth_flow.py`: Registration, duplicate email rejection, login, access token verification, refresh cookie rotation, logout revocation.
  - `test_document_lifecycle.py`: Multipart file upload, magic byte validation, storage key generation, extraction triggering, document deletion.
  - `test_analysis_orchestration.py`: Triggering analysis, mocked Gemini extraction, deterministic rule invocation, step persistence in `analysis_steps`.
  - `test_review_workflow.py`: Review task retrieval, status transitions, approval, rejection with mandatory comments, optimistic locking conflict detection.
  - `test_audit_persistence.py`: Ensuring that each lifecycle action generates an immutable audit record.

---

## 4. Security Penetration Test Suite

- **Directory:** `tests/security/`
- **Target Vulnerabilities:**
  - `test_bola_authorization.py`: User A creates Document A. User B attempts `GET /api/v1/documents/{A.id}` and `DELETE /api/v1/documents/{A.id}` $\to$ Must return `404 Not Found`.
  - `test_unauthorized_review.py`: Normal `USER` attempts to post a decision to `/api/v1/reviews/{id}/decision` $\to$ Must return `403 Forbidden`.
  - `test_reviewer_self_approval.py`: Reviewer uploads a policy, then attempts to approve findings on their own document $\to$ Must return `403 Forbidden`.
  - `test_token_replay.py`: Presenting an already-revoked refresh token $\to$ Must revoke the entire token family and return `401 Unauthorized`.
  - `test_path_traversal.py`: Uploading a file named `../../../../etc/shadow` $\to$ Must be saved safely as `<uuid>.dat` in storage root.
  - `test_file_size_abuse.py`: Uploading a file exceeding 25 MB $\to$ Must abort immediately with `400 Bad Request`.

---

## 5. End-to-End Acceptance Test Scenario (Part 24 Verification)

An automated suite (`tests/e2e/test_acceptance_scenario.py`) validates the 20-step master acceptance scenario:
1. Register user `analyst@test.com`.
2. Login and acquire JWT + refresh cookie.
3. Upload valid `sample_expense_policy.pdf`.
4. Validate SHA-256 and private storage creation.
5. Extract text page-by-page.
6. Verify persistence in `document_extractions`.
7. Trigger `POST /documents/{id}/analyze`.
8. Create `analysis_runs` record with status `RUNNING`.
9. Ingest mock Gemini structured response.
10. Validate extraction against Pydantic schema.
11. Execute `Tool 1` and `Tool 2` and persist steps.
12. Execute `Tool 3` (Deterministic compliance engine).
13. Verify generated findings with exact quotes and page references.
14. Queue findings into `review_tasks` with status `OPEN`.
15. Login as `reviewer@test.com`.
16. Retrieve review queue and inspect evidence.
17. Reviewer executes `POST /reviews/{id}/decision` with `APPROVED` and commentary.
18. Verify review status transitions to `COMPLETED`.
19. Verify immutable `audit_events` row generated for review decision.
20. Confirm historical analysis run remains intact and un-overwritten.
