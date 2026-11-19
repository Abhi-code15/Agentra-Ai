# Agentra AI — Enterprise Policy Intelligence & Reimbursement Platform

> **Automated verification of employee reimbursement claims against official company policies.**  
> *Deterministic rules. Human oversight. Zero guesswork.*

---

## 1. What is Agentra AI?

Every company has its own rules for expenses, travel, meals, procurement, and leave. Traditionally, finance teams spend hours manually reading PDF policy handbooks, checking receipts line-by-line, and verifying that spending limits weren't exceeded.

**Agentra AI automates this entire verification lifecycle:**
1. **Upload Company Policy:** Finance managers upload their official company policy documents (PDF or DOCX).
2. **AI Rule Extraction:** Agentra extracts spending limits, receipt requirements, and approval rules directly from the document text.
3. **Manager Verification:** An authorized reviewer approves the extracted rules, making them the active company standard.
4. **Employee Submission:** Employees submit reimbursement claims, itemize expenses (meals, lodging, travel, supplies), and attach receipts.
5. **Deterministic Policy Check:** A deterministic Python rule engine immediately compares the submitted expenses against the approved company limits.
6. **Manager Approval & Official Voucher:** Authorized managers review any exceptions in their review queue and approve claims. Once approved, the platform generates an **Official Reimbursement Approval Voucher** ready for payroll and direct deposit payout.

```
       [Company Policy PDF]
                │
                ▼ (AI Extraction)
     [Approved Spending Rules] ───┐
                                  │
[Employee Reimbursement Claim]    ▼
[Itemized Bills & Receipts]   ──> [Deterministic Python Rule Engine]
                                  │
                                  ▼
                         [Instant Policy Check]
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
         [Compliant Claim]                 [Limit Exceeded]
                 │                                 │
                 ▼                                 ▼
      [One-Click Manager Review]         [Manager Review Queue]
                 │                                 │
                 └────────────────┬────────────────┘
                                  ▼
                [Official Reimbursement Voucher]
             (Authorized for Direct Deposit & Payroll)
```

---

## 2. What's New: Improvements in This Version vs Older Version

This release represents a complete architectural evolution of Agentra. We eliminated unnecessary developer debug traces, simplified technical jargon into everyday business language, enforced strict role separation, and added a dedicated reimbursement approval voucher.

| Capability | Older Version | New Version (Current) |
| :--- | :--- | :--- |
| **Primary Focus** | Generic document parser with mock loan and HR text. | **Laser-focused on Enterprise Reimbursement Intelligence** (Travel, Meals, Procurement, and Business Expenses). |
| **Developer Clutter** | Showed raw `Agent Execution Telemetry` with empty `TOOL INPUT` and `TOOL OUTPUT` debug boxes in user screens. | **Completely Removed.** Replaced with clean spending allowance cards and a friendly 4-stage policy readiness checklist. |
| **Approved Voucher UI** | No payout or voucher interface after approval. | **Dedicated Official Reimbursement Approval Voucher** with authorized payment seal, direct deposit routing, manager approval sign-off, and print/save PDF capability. |
| **Role Isolation** | Unclear navigation where regular employees could see raw document tables and review queues. | **Strict Role Separation:**<br>• **Employees (`USER`):** Only see Dashboard, New Reimbursement, My Reimbursements, and Company Limits.<br>• **Reviewers (`REVIEWER`):** See Review Queue, All Claims, Company Policy Management, and Activity History. |
| **Authentication & Login** | Confusing login with a bottom "Quick Fill Demo Credentials" box. | **Clean Portal Selection:** Interactive portal switch at login (`Employee Portal` vs `Finance Reviewer Portal`) with explicit role badges and clear credentials. |
| **Policy Detail Screen** | Prone to blank white screens when viewing newly created draft policies. | **Bulletproof Policy Detail:** Added safe accessors, instant rule approval/rejection, AI rule extraction, and a global React `ErrorBoundary`. |
| **Language & Jargon** | Heavy developer jargon ("bounded telemetry", "magic byte validation", "deterministic adjudication"). | **Simple, Familiar Business Language** that employees and finance managers can immediately understand. |
| **AI Reliability** | Long latency and hang when API keys were misconfigured. | **Instant Circuit Breaker (<50ms):** Automatically falls back to high-speed local keyword synthesis if the external AI key is invalid or unavailable. |
| **Test Coverage** | Partial test suite with potential schema mismatches. | **100% Green Test Suite:** 38 integration, security, and rule-engine tests passing in ~11s. Zero Vite compilation errors. |

---

## 3. The Two User Workflows

Agentra provides two distinct, tailored workflow loops: one for employees submitting claims and one for finance managers governing policies.

### A. Employee Reimbursement Flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ 1. Choose Policy │ ──> │ 2. Enter Bills   │ ──> │ 3. Attach Proof  │ ──> │ 4. Policy Check  │ ──> │ 5. Approved &    │
│    Standard      │     │    & Amounts     │     │    Receipts      │     │    Results       │     │    Paid (Voucher)│
└──────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
```

1. **Choose Policy:** Employee selects the relevant company policy (e.g., Acme Travel & Expense Policy).
2. **Enter Bills:** Itemizes individual expenses (Meals, Lodging, Transport, Office Supplies) with dates and amounts.
3. **Attach Proof:** Uploads receipt images or PDFs.
4. **Policy Check:** The system automatically verifies line items against company spending limits and receipt rules.
5. **Approved & Paid:** Once approved by a manager, the employee receives an **Official Reimbursement Approval Voucher** indicating that payment is queued for direct deposit.

---

### B. Finance Reviewer Governance Cycle

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ 1. Upload Policy │ ──> │ 2. AI Extraction │ ──> │ 3. Auto-Check    │ ──> │ 4. Manager       │ ──> │ 5. Disbursement  │
│    Document      │     │    & Set Limits  │     │    Employee Bills│     │    Decision      │     │    Voucher Issued│
└──────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
```

1. **Upload Policy:** Finance reviewer uploads an official company policy PDF (e.g., `Employee-Expense-Policy-2024.pdf`).
2. **AI Extraction & Limit Verification:** The system extracts daily meal allowances, hotel room rate caps, mileage rates, and receipt thresholds. The reviewer can edit or approve each rule.
3. **Auto-Check Bills:** Incoming employee claims are automatically checked against the approved rules.
4. **Manager Decision:** Claims matching all rules can be approved with one click; claims exceeding limits are flagged in the **Review Queue** with exact policy citations.
5. **Disbursement:** Approving a claim issues an official payout voucher and records an immutable entry in the activity audit trail.

---

## 4. Real-World Walkthrough Examples

### Example 1: Compliant Business Lunch & Hotel Stay

* **Employee:** Jane Doe (Sales)
* **Submitted Expenses:**
  * Client Dinner: `$64.00 USD` (Receipt attached)
  * Hotel Stay: `$210.00 USD / night` (Receipt attached)
* **Company Policy Standard:**
  * Meal Allowance Cap: `$75.00 USD / day`
  * Lodging Cap: `$250.00 USD / night`
  * Receipt Mandate: Required for any expense above `$25.00`
* **Agentra Verification Output:**
  * `[PASS]` Client Dinner (`$64.00`) is within the daily meal limit of `$75.00`.
  * `[PASS]` Hotel Stay (`$210.00`) is within standard lodging rate limit of `$250.00`.
  * `[PASS]` Itemized receipts verified for both items.
  * **Result:** `All Checks Passed`. Fast-tracked to manager approval.

---

### Example 2: Flagged Policy Warning (Exceeded Limit)

* **Employee:** Alex Smith (Engineering)
* **Submitted Expense:**
  * Team Dinner: `$120.00 USD`
* **Agentra Verification Output:**
  * `[WARNING - EXCEEDS LIMIT]` Rule `EXP-MEAL-CAP`: Total meal expense of `$120.00` exceeds the allowable daily cap of `$75.00`.
  * **Verified Policy Citation:**
    > *"Daily employee meal expenses must not exceed $75.00 per diem without prior department director sign-off."* — Page 3, Section 2.1
  * **Manager Action:** The claim is routed to the **Review Queue**. The manager can either approve the exception with notes or request revisions from the employee.

---

### Example 3: Approved Reimbursement Voucher

When a claim is approved, Agentra presents an official payment voucher:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       REIMBURSEMENT APPROVAL VOUCHER                        │
│            Voucher #EXP-2026-0042 • Authorized for Corporate Payout         │
├─────────────────────────────────────────────────────────────────────────────┤
│  AUTHORIZED PAYOUT: $284.50 USD                 STATUS: [ AUTHORIZED / PAID ]│
│  DISBURSEMENT METHOD: Direct Deposit / Payroll  APPROVAL: Finance Reviewer  │
├─────────────────────────────────────────────────────────────────────────────┤
│  VERIFIED LINE ITEMS:                                                       │
│  • Client Dinner (Meals)               $74.50  [✓ Verified & Compliant]     │
│  • Office Supplies (Procurement)      $210.00  [✓ Verified & Compliant]     │
├─────────────────────────────────────────────────────────────────────────────┤
│  MANAGER NOTE: "Approved under quarterly sales development budget."         │
│  [ Print / Save PDF Voucher ]                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Technology Stack

* **Backend Framework:** Python 3.12, FastAPI (REST API with asynchronous request lifecycle).
* **Database & ORM:** PostgreSQL 15+, SQLAlchemy 2.0 (Mapped type-safe models), Alembic migrations.
* **Security & Auth:** Argon2id password hashing, rotating JWT access tokens, HttpOnly refresh cookies, tenant boundary authorization.
* **Deterministic Rule Engine:** Custom Python rule evaluation engine running mathematical, threshold, and existence comparisons (no LLM hallucinations in compliance math).
* **AI Integration:** Google Gemini API (`gemini-2.5-flash`) for natural language parameter extraction with delimited prompt boundaries and structured JSON schemas.
* **Frontend:** React 18, Vite 5, Tailwind CSS, Lucide Icons, React Router v6.
* **Test Harness:** pytest, pytest-asyncio, HTTPX TestClient.

---

## 6. Architecture & System Flow

```
┌────────────────────────────────────────────────────────┐
│               REACT 18 SINGLE PAGE APP                 │
│  (Employee Portal | Finance Reviewer Portal | Voucher) │
└───────────────────────────┬────────────────────────────┘
                            │ HTTPS / REST JSON
┌───────────────────────────▼────────────────────────────┐
│                    FASTAPI BACKEND                     │
│  ┌────────────────────┐      ┌──────────────────────┐  │
│  │ Auth & Tenant Auth │      │ Policy & Claim APIs  │  │
│  └─────────┬──────────┘      └──────────┬───────────┘  │
│            │                            │              │
│  ┌─────────▼────────────────────────────▼───────────┐  │
│  │           DETERMINISTIC RULE ENGINE              │  │
│  │  (Python comparisons: caps, dates, receipts)      │  │
│  └─────────┬────────────────────────────┬───────────┘  │
│            │                            │              │
│  ┌─────────▼──────────┐      ┌──────────▼───────────┐  │
│  │ Google Gemini SDK  │      │ PostgreSQL Database  │  │
│  │ (Clause Extraction)│      │ (Multi-Tenant Store) │  │
│  └────────────────────┘      └──────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## 7. Quickstart Setup Guide

### Prerequisites
* **Python 3.12+**
* **Node.js 18+**
* **PostgreSQL 15+** (Local service or Docker container)

---

### Step 1: Backend Setup (PowerShell)

```powershell
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate Python 3.12 virtual environment
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
Copy-Item .env.example .env
# Open .env and set your DATABASE_URL and GEMINI_API_KEY (optional)

# 5. Run database migrations
alembic upgrade head

# 6. Start the API server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The FastAPI backend will start at `http://127.0.0.1:8000`.  
Swagger interactive API docs will be available at `http://127.0.0.1:8000/docs`.

---

### Step 2: Frontend Setup (PowerShell)

```powershell
# Open a new terminal and navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

Visit the application at `http://localhost:5173`.

---

### Step 3: Running Tests

To verify backend integrity, run the complete test suite:

```powershell
.\backend\venv\Scripts\python.exe -m pytest -v backend\tests
```
**Result:** 38 passed, 0 failed in ~11 seconds.

To test the frontend build:
```powershell
npm --prefix frontend run build
```
**Result:** Vite production bundle created with zero errors.

---

## 8. Default Login Portals

When opening `http://localhost:5173/login`, you can choose between two portal modes:

| Portal | Role | Email | Password | Primary Actions |
| :--- | :--- | :--- | :--- | :--- |
| **Employee Portal** | `USER` | `employee@agentra.internal` | `Password123!` | Submit reimbursement claims, upload receipts, view policy limits, view approved vouchers. |
| **Reviewer Portal** | `REVIEWER` | `reviewer@agentra.internal` | `Password123!` | Review pending claims, approve/reject vouchers, upload policy standards, extract AI rules. |

*(New accounts can also be created at any time on the `/register` page with either role.)*

---

## 9. Security & Compliance Principles

1. **Deterministic Rule Sovereignty:** AI models extract clauses and numbers, but compliance decisions are strictly calculated by deterministic Python logic. An LLM never makes the final financial approval.
2. **Grounded Provenance:** Every rule violation points to exact text in the uploaded policy standard so employees and managers understand why an item was flagged.
3. **Multi-Tenant Isolation:** All database queries are scoped to the active organization ID. Employees cannot view other employees' claims unless granted reviewer permissions.
4. **Immutable Audit Ledger:** Every rule check, submission, manager approval, and rejection is recorded with timestamps, user IDs, and client IP addresses in the audit ledger.

---

## 10. License

Agentra AI is licensed under the Apache 2.0 License.
