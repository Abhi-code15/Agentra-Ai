"""End-to-End Master Acceptance Test Scenario (Part 24 Verification).

Executes the complete 20-step end-to-end governance lifecycle from user registration
to upload, AI extraction, deterministic rule checks, finding generation, human review,
and audit trail verification.
"""
import io
import uuid
from unittest.mock import MagicMock, patch
import pytest
import pymupdf
from fastapi.testclient import TestClient

from app.integrations.gemini.schemas import (
    ApprovalTierSchema,
    DocumentationRequirementSchema,
    ExpensePolicyExtractionSchema,
)


def create_demo_expense_policy_pdf() -> io.BytesIO:
    doc = pymupdf.open()
    page = doc.new_page()
    text = (
        "Enterprise Global Travel & Expense Policy 2026\n\n"
        "1. Approval Limits:\n"
        "   - Operational expenses up to INR 7,500 may be approved by Department Managers.\n"
        "   - Expenses up to INR 10,000 require Finance Director approval.\n"
        "   - Expenses exceeding INR 10,000 require Senior VP approval.\n\n"
        "2. Documentation & Compliance:\n"
        "   - Valid itemized tax invoice is mandatory for all claims.\n"
        "   - Claims must be submitted within 30 days of expense occurrence."
    )
    page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return io.BytesIO(pdf_bytes)


def test_master_acceptance_scenario_20_steps(client: TestClient) -> None:
    """Executes and verifies all 20 steps of the Master Engineering Specification acceptance criteria."""
    # -------------------------------------------------------------------------
    # Step 1: A user registers
    # -------------------------------------------------------------------------
    analyst_email = f"analyst_{uuid.uuid4().hex[:8]}@corp.com"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": analyst_email,
            "full_name": "Senior Policy Analyst",
            "password": "SecurePassword!2026",
            "role": "USER",
        },
    )
    assert reg_res.status_code == 201
    user_id = reg_res.json()["data"]["id"]

    # -------------------------------------------------------------------------
    # Step 2: The user logs in
    # -------------------------------------------------------------------------
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": analyst_email, "password": "SecurePassword!2026"},
    )
    assert login_res.status_code == 200
    access_token = login_res.json()["data"]["access_token"]
    user_headers = {"Authorization": f"Bearer {access_token}"}
    assert "refresh_token" in login_res.cookies

    # -------------------------------------------------------------------------
    # Step 3 & 4: Upload valid expense policy PDF & validate/store file
    # -------------------------------------------------------------------------
    pdf_stream = create_demo_expense_policy_pdf()
    upload_res = client.post(
        "/api/v1/documents",
        files={"file": ("Global_Expense_Policy_2026.pdf", pdf_stream, "application/pdf")},
        headers=user_headers,
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["data"]["id"]

    # -------------------------------------------------------------------------
    # Step 5 & 6: Document text extracted and extraction persisted
    # -------------------------------------------------------------------------
    doc_detail_res = client.get(f"/api/v1/documents/{doc_id}", headers=user_headers)
    assert doc_detail_res.status_code == 200
    doc_data = doc_detail_res.json()["data"]
    assert doc_data["document_status"] == "READY_FOR_ANALYSIS"
    assert doc_data["extraction"] is not None
    assert doc_data["extraction"]["extraction_status"] == "COMPLETED"

    # -------------------------------------------------------------------------
    # Step 7 & 8: User initiates analysis & backend creates analysis record
    # Step 9 & 10: Gemini returns structured output & Pydantic validates result
    # Step 11 & 12: Agent invokes tools & compliance engine evaluates rules
    # Step 13 & 14: Findings generated with evidence & routed for human review
    # -------------------------------------------------------------------------
    # Note: Manager limit is 7,500 INR in the policy, but the predefined rule ceiling is 5,000 INR!
    mock_gemini_extraction = ExpensePolicyExtractionSchema(
        document_type="EXPENSE_REIMBURSEMENT_POLICY",
        document_title="Enterprise Global Travel & Expense Policy 2026",
        effective_date="2026-01-01",
        approval_tiers=[
            ApprovalTierSchema(
                tier_name="Tier 1",
                approver_role="Department Manager",
                minimum_amount=0.0,
                maximum_amount=7500.0,  # VIOLATION of 5,000 ceiling!
                currency="INR",
                source_page=1,
                evidence_quote="Operational expenses up to INR 7,500 may be approved by Department Managers.",
            ),
            ApprovalTierSchema(
                tier_name="Tier 2",
                approver_role="Finance",
                minimum_amount=5001.0,
                maximum_amount=10000.0,
                currency="INR",
                source_page=1,
                evidence_quote="Expenses up to INR 10,000 require Finance Director approval.",
            ),
        ],
        required_documentation=[
            DocumentationRequirementSchema(
                document_name="Tax Invoice",
                is_mandatory=True,
                submission_window_days=30,
                source_page=1,
                evidence_quote="Valid itemized tax invoice is mandatory for all claims.",
            )
        ],
        potential_ambiguities=[],
    )

    with patch("app.tools.compliance_tools.GeminiClient") as MockGemini:
        mock_instance = MagicMock()
        mock_instance.extract_structured_policy.return_value = mock_gemini_extraction
        MockGemini.return_value = mock_instance

        analyze_res = client.post(f"/api/v1/documents/{doc_id}/analyze", headers=user_headers)
        assert analyze_res.status_code == 202
        analysis_id = analyze_res.json()["data"]["analysis_run_id"]
        assert analyze_res.json()["data"]["status"] == "COMPLETED"

    # Verify Steps and Findings
    steps_res = client.get(f"/api/v1/analyses/{analysis_id}/steps", headers=user_headers)
    assert steps_res.status_code == 200
    assert len(steps_res.json()["data"]) >= 4

    findings_res = client.get(f"/api/v1/analyses/{analysis_id}/findings", headers=user_headers)
    assert findings_res.status_code == 200
    findings = findings_res.json()["data"]
    assert len(findings) >= 1

    violation_finding = next((f for f in findings if f["finding_type"] == "violation"), None)
    assert violation_finding is not None
    assert "EXP_RULE_MANAGER_TIER" in violation_finding["finding_code"]
    assert violation_finding["status"] == "PENDING_REVIEW"
    assert "7,500" in violation_finding["evidence"]["quote"]

    # -------------------------------------------------------------------------
    # Step 15: Authorized reviewer opens review task
    # -------------------------------------------------------------------------
    reviewer_email = f"lead_reviewer_{uuid.uuid4().hex[:8]}@corp.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": reviewer_email, "full_name": "Chief Governance Auditor", "password": "Password123!", "role": "REVIEWER"},
    )
    rev_login = client.post("/api/v1/auth/login", json={"email": reviewer_email, "password": "Password123!"})
    rev_token = rev_login.json()["data"]["access_token"]
    reviewer_headers = {"Authorization": f"Bearer {rev_token}"}

    queue_res = client.get("/api/v1/reviews?status=OPEN", headers=reviewer_headers)
    assert queue_res.status_code == 200
    tasks = queue_res.json()["data"]
    target_task = next((t for t in tasks if t["finding_id"] == violation_finding["id"]), None)
    assert target_task is not None
    task_id = target_task["id"]

    # -------------------------------------------------------------------------
    # Step 16 & 17: Reviewer approves finding & database stores decision
    # -------------------------------------------------------------------------
    decision_res = client.post(
        f"/api/v1/reviews/{task_id}/decision",
        json={
            "decision": "APPROVED",
            "reviewer_comments": "Verified non-compliant INR 7,500 threshold against Governance Standard Rule 1.",
        },
        headers=reviewer_headers,
    )
    assert decision_res.status_code == 200
    decision_data = decision_res.json()["data"]
    assert decision_data["status"] == "COMPLETED"
    assert decision_data["decision"] == "APPROVED"

    # -------------------------------------------------------------------------
    # Step 18: Audit event records the decision
    # -------------------------------------------------------------------------
    audit_res = client.get(
        f"/api/v1/audit-events?event_type=REVIEW_DECISION_SUBMITTED&entity_id={task_id}",
        headers=reviewer_headers,
    )
    assert audit_res.status_code == 200
    audit_records = audit_res.json()["data"]
    assert len(audit_records) == 1
    assert audit_records[0]["event_type"] == "REVIEW_DECISION_SUBMITTED"
    assert audit_records[0]["event_metadata"]["decision"] == "APPROVED"

    # -------------------------------------------------------------------------
    # Step 19: API / UI displays updated state
    # -------------------------------------------------------------------------
    finding_check = client.get(f"/api/v1/findings/{violation_finding['id']}", headers=user_headers)
    assert finding_check.status_code == 200
    assert finding_check.json()["data"]["status"] == "APPROVED"

    # -------------------------------------------------------------------------
    # Step 20: Application preserves complete analysis history
    # -------------------------------------------------------------------------
    history_res = client.get(f"/api/v1/analyses/{analysis_id}", headers=user_headers)
    assert history_res.status_code == 200
    history_data = history_res.json()["data"]
    assert history_data["id"] == analysis_id
    assert history_data["status"] == "COMPLETED"
    assert history_data["findings_count"] >= 1
    assert history_data["steps_count"] >= 4
