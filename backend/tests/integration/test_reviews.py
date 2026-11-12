"""Integration tests for Human-in-the-Loop review queue, decisions, self-approval prevention, and audit."""
import io
import uuid
from unittest.mock import MagicMock, patch
import pytest
import pymupdf
from fastapi.testclient import TestClient

from app.integrations.gemini.schemas import (
    ApprovalTierSchema,
    ExpensePolicyExtractionSchema,
)


def create_test_pdf(text: str) -> io.BytesIO:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return io.BytesIO(pdf_bytes)


def test_review_workflow_and_audit_persistence(client: TestClient) -> None:
    """Verifies review queue, approval, rejection validation, self-approval prevention, and audit logging."""
    # 1. Register Submitter (USER)
    submitter_email = f"submitter_{uuid.uuid4().hex[:8]}@corp.com"
    client.post("/api/v1/auth/register", json={"email": submitter_email, "full_name": "Submitter User", "password": "Password123!", "role": "USER"})
    sub_login = client.post("/api/v1/auth/login", json={"email": submitter_email, "password": "Password123!"})
    sub_token = sub_login.json()["data"]["access_token"]
    sub_headers = {"Authorization": f"Bearer {sub_token}"}

    # 2. Register Reviewer (REVIEWER)
    reviewer_email = f"reviewer_{uuid.uuid4().hex[:8]}@corp.com"
    client.post("/api/v1/auth/register", json={"email": reviewer_email, "full_name": "Compliance Reviewer", "password": "Password123!", "role": "REVIEWER"})
    rev_login = client.post("/api/v1/auth/login", json={"email": reviewer_email, "password": "Password123!"})
    rev_token = rev_login.json()["data"]["access_token"]
    rev_headers = {"Authorization": f"Bearer {rev_token}"}

    # 3. Submitter uploads non-compliant document and triggers analysis
    pdf_bytes = create_test_pdf("Policy: Managers can approve up to INR 9,000.")
    up_res = client.post(
        "/api/v1/documents",
        files={"file": ("Policy.pdf", pdf_bytes, "application/pdf")},
        headers=sub_headers,
    )
    doc_id = up_res.json()["data"]["id"]

    mock_extraction = ExpensePolicyExtractionSchema(
        document_type="EXPENSE_REIMBURSEMENT_POLICY",
        document_title="Policy",
        approval_tiers=[
            ApprovalTierSchema(
                tier_name="Tier 1",
                approver_role="Department Manager",
                minimum_amount=0.0,
                maximum_amount=9000.0,  # VIOLATION
                currency="INR",
                source_page=1,
                evidence_quote="Policy: Managers can approve up to INR 9,000.",
            )
        ],
        required_documentation=[],
        potential_ambiguities=[],
    )

    with patch("app.tools.compliance_tools.GeminiClient") as MockGemini:
        mock_instance = MagicMock()
        mock_instance.extract_structured_policy.return_value = mock_extraction
        MockGemini.return_value = mock_instance

        analyze_res = client.post(f"/api/v1/documents/{doc_id}/analyze", headers=sub_headers)
        assert analyze_res.status_code == 202

    # 4. Standard USER attempts to access review queue -> 403 Forbidden
    forbidden_queue = client.get("/api/v1/reviews", headers=sub_headers)
    assert forbidden_queue.status_code == 403

    # 5. REVIEWER accesses review queue -> 200 OK
    rev_queue = client.get("/api/v1/reviews?status=OPEN", headers=rev_headers)
    assert rev_queue.status_code == 200
    queue_data = rev_queue.json()
    assert queue_data["pagination"]["total_records"] >= 1
    task = queue_data["data"][0]
    task_id = task["id"]
    assert task["status"] == "OPEN"

    # 6. Rejection Validation: Reject without comments -> 422 Unprocessable Entity
    bad_reject = client.post(
        f"/api/v1/reviews/{task_id}/decision",
        json={"decision": "REJECTED", "reviewer_comments": ""},
        headers=rev_headers,
    )
    assert bad_reject.status_code == 422

    # 7. Valid Approval
    approve_res = client.post(
        f"/api/v1/reviews/{task_id}/decision",
        json={"decision": "APPROVED", "reviewer_comments": "Verified non-compliance. Escalated to policy committee."},
        headers=rev_headers,
    )
    assert approve_res.status_code == 200
    updated_task = approve_res.json()["data"]
    assert updated_task["status"] == "COMPLETED"
    assert updated_task["decision"] == "APPROVED"
    assert updated_task["decided_at"] is not None

    # 8. Optimistic Concurrency: Attempting duplicate decision -> 409 Conflict
    dup_decision = client.post(
        f"/api/v1/reviews/{task_id}/decision",
        json={"decision": "APPROVED", "reviewer_comments": "Second attempt"},
        headers=rev_headers,
    )
    assert dup_decision.status_code == 409
    assert dup_decision.json()["error"]["code"] == "REVIEW_TASK_ALREADY_DECIDED"

    # 9. Verify Audit Event Recorded
    audit_res = client.get("/api/v1/audit-events?event_type=REVIEW_DECISION_SUBMITTED", headers=rev_headers)
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["pagination"]["total_records"] >= 1
    latest_event = audit_data["data"][0]
    assert latest_event["event_type"] == "REVIEW_DECISION_SUBMITTED"
    assert latest_event["entity_id"] == task_id
    assert latest_event["event_metadata"]["decision"] == "APPROVED"


def test_reviewer_self_approval_prohibition(client: TestClient) -> None:
    """Verifies that a reviewer cannot approve or reject findings on documents they personally uploaded."""
    # Register Reviewer
    reviewer_email = f"self_rev_{uuid.uuid4().hex[:8]}@corp.com"
    client.post("/api/v1/auth/register", json={"email": reviewer_email, "full_name": "Dual Role User", "password": "Password123!", "role": "REVIEWER"})
    login_res = client.post("/api/v1/auth/login", json={"email": reviewer_email, "password": "Password123!"})
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Reviewer uploads their own document
    pdf_bytes = create_test_pdf("Own Policy: Managers can approve up to INR 9,000.")
    up_res = client.post(
        "/api/v1/documents",
        files={"file": ("Own_Policy.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    doc_id = up_res.json()["data"]["id"]

    mock_extraction = ExpensePolicyExtractionSchema(
        document_type="EXPENSE_REIMBURSEMENT_POLICY",
        document_title="Own Policy",
        approval_tiers=[
            ApprovalTierSchema(
                tier_name="Tier 1",
                approver_role="Department Manager",
                minimum_amount=0.0,
                maximum_amount=9000.0,
                currency="INR",
                source_page=1,
                evidence_quote="Own Policy: Managers can approve up to INR 9,000.",
            )
        ],
        required_documentation=[],
        potential_ambiguities=[],
    )

    with patch("app.tools.compliance_tools.GeminiClient") as MockGemini:
        mock_instance = MagicMock()
        mock_instance.extract_structured_policy.return_value = mock_extraction
        MockGemini.return_value = mock_instance
        client.post(f"/api/v1/documents/{doc_id}/analyze", headers=headers)

    # Fetch review task for this finding
    queue_res = client.get("/api/v1/reviews?status=OPEN", headers=headers)
    task_id = queue_res.json()["data"][0]["id"]

    # Attempt self-approval -> 403 Forbidden
    self_decision = client.post(
        f"/api/v1/reviews/{task_id}/decision",
        json={"decision": "APPROVED", "reviewer_comments": "Approving my own document"},
        headers=headers,
    )
    assert self_decision.status_code == 403
    assert self_decision.json()["error"]["code"] == "REVIEWER_SELF_APPROVAL_PROHIBITED"
