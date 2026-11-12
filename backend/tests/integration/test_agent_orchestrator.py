"""Integration test for end-to-end agent orchestration, rule evaluation, and finding generation."""
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


def create_policy_pdf(text: str) -> io.BytesIO:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return io.BytesIO(pdf_bytes)


def test_agent_orchestration_and_finding_generation(client: TestClient) -> None:
    """Verifies that the agent executes 4 steps, evaluates rules, and persists findings."""
    # 1. Register and Authenticate User
    email = f"analyst_{uuid.uuid4().hex[:8]}@corp.com"
    client.post("/api/v1/auth/register", json={"email": email, "full_name": "Senior Analyst", "password": "Password123!"})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload Document with Non-Compliant Manager Limit (8,000 INR > 5,000 INR limit)
    policy_text = (
        "Corporate Travel Policy 2026.\n"
        "Section 1: Approval Limits.\n"
        "Department Managers may approve reimbursements up to INR 8,000.\n"
        "Claims over INR 10,000 require VP approval."
    )
    pdf_file = create_policy_pdf(policy_text)
    upload_res = client.post(
        "/api/v1/documents",
        files={"file": ("Travel_Policy.pdf", pdf_file, "application/pdf")},
        headers=headers,
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["data"]["id"]

    # 3. Mock Gemini Extraction Result
    mock_extraction = ExpensePolicyExtractionSchema(
        document_type="EXPENSE_REIMBURSEMENT_POLICY",
        document_title="Corporate Travel Policy 2026",
        approval_tiers=[
            ApprovalTierSchema(
                tier_name="Tier 1",
                approver_role="Department Manager",
                minimum_amount=0.0,
                maximum_amount=8000.0,  # VIOLATION! (Ceiling is 5,000)
                currency="INR",
                source_page=1,
                evidence_quote="Department Managers may approve reimbursements up to INR 8,000.",
            )
        ],
        required_documentation=[],  # MISSING RECEIPT REQUIREMENT!
        potential_ambiguities=[],
    )

    with patch("app.tools.compliance_tools.GeminiClient") as MockGemini:
        mock_instance = MagicMock()
        mock_instance.extract_structured_policy.return_value = mock_extraction
        MockGemini.return_value = mock_instance

        # 4. Trigger Analysis
        analyze_res = client.post(f"/api/v1/documents/{doc_id}/analyze", headers=headers)
        assert analyze_res.status_code == 202
        analysis_data = analyze_res.json()["data"]
        analysis_id = analysis_data["analysis_run_id"]
        assert analysis_data["status"] == "COMPLETED"

    # 5. Verify Execution Steps Telemetry
    steps_res = client.get(f"/api/v1/analyses/{analysis_id}/steps", headers=headers)
    assert steps_res.status_code == 200
    steps = steps_res.json()["data"]
    assert len(steps) >= 4  # Steps 1 to 4 executed
    step_tools = [s["tool_name"] for s in steps if s["tool_name"]]
    assert "extract_document_information" in step_tools
    assert "retrieve_document_evidence" in step_tools
    assert "evaluate_compliance_rules" in step_tools
    assert "create_review_findings" in step_tools

    # 6. Verify Generated Findings
    findings_res = client.get(f"/api/v1/analyses/{analysis_id}/findings", headers=headers)
    assert findings_res.status_code == 200
    findings = findings_res.json()["data"]
    assert len(findings) >= 2

    # Check for Violation Finding
    violation = next((f for f in findings if f["finding_type"] == "violation"), None)
    assert violation is not None
    assert "EXP_RULE_MANAGER_TIER" in violation["finding_code"]
    assert violation["severity"] == "HIGH"
    assert "8,000" in violation["evidence"]["quote"]

    # Check for Missing Requirement Findings
    missing_codes = [f["finding_code"] for f in findings if f["finding_type"] == "missing_requirement"]
    assert any("EXP_RULE_RECEIPT_MANDATORY" in code for code in missing_codes)
    assert any("EXP_RULE_FINANCE_TIER" in code for code in missing_codes)

    # 7. Query Global Findings Endpoint
    all_findings_res = client.get("/api/v1/findings?status=PENDING_REVIEW", headers=headers)
    assert all_findings_res.status_code == 200
    assert all_findings_res.json()["pagination"]["total_records"] >= 2
