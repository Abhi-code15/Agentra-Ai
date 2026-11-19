"""Integration tests for Multi-Tenant Policies, Rule Ingestion, Claims, and Deterministic Evaluation."""
import io
import uuid
from datetime import date
from fastapi.testclient import TestClient
import pymupdf


def create_test_pdf_file(text: str = "Test Policy Document") -> io.BytesIO:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return io.BytesIO(pdf_bytes)


def get_authenticated_headers(client: TestClient, role: str = "USER") -> dict:
    email = f"user_{role.lower()}_{uuid.uuid4().hex[:8]}@corp.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": f"Test {role.title()}", "password": "Password123!", "role": role},
    )
    assert reg.status_code == 201

    login = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_organization_and_policy_lifecycle(client: TestClient) -> None:
    """Verifies organization creation, policy standard creation, rule extraction, and version activation."""
    admin_headers = get_authenticated_headers(client, role="ADMIN")

    # 1. Create Organization
    org_slug = f"acme-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/v1/organizations",
        json={"name": "Acme Global Corp", "slug": org_slug, "domain": "acme.com"},
        headers=admin_headers,
    )
    assert res.status_code == 201
    org_data = res.json()["data"]
    org_id = org_data["id"]

    org_headers = {**admin_headers, "X-Organization-Id": org_id}

    # 2. Upload a policy standard document
    policy_text = (
        "Global Corporate Expense Policy 2026.\n"
        "Section 3.1: Individual meals are reimbursed up to $50.00 per meal.\n"
        "Section 3.2: Hotel accommodation is capped at $150.00 per night.\n"
        "Section 4.0: Original itemized tax invoices and receipts are mandatory for all claims.\n"
        "Section 5.0: Expenses must be submitted within 30 days of occurrence."
    )
    pdf_file = create_test_pdf_file(policy_text)
    upload_res = client.post(
        "/api/v1/documents",
        files={"file": ("Global_Expense_Policy_2026.pdf", pdf_file, "application/pdf")},
        headers=org_headers,
    )
    assert upload_res.status_code == 201
    document_id = upload_res.json()["data"]["id"]

    # 3. Create Policy linking the standard document
    pol_res = client.post(
        f"/api/v1/policies?document_id={document_id}",
        json={
            "name": "Global Travel & Expense Policy 2026",
            "category": "EXPENSE",
            "description": "Standard rules governing employee meals, lodging, and transport reimbursements.",
        },
        headers=org_headers,
    )
    assert pol_res.status_code == 201
    policy_data = pol_res.json()["data"]
    policy_id = policy_data["id"]

    # 4. Retrieve policy detail with versions and extracted rules
    detail_res = client.get(f"/api/v1/policies/{policy_id}", headers=org_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()["data"]
    assert detail["name"] == "Global Travel & Expense Policy 2026"
    assert len(detail["versions"]) >= 1
    version_id = detail["versions"][0]["id"]

    # 5. Extract rules via API
    extract_res = client.post(f"/api/v1/policies/versions/{version_id}/extract", headers=org_headers)
    assert extract_res.status_code == 200
    rules = extract_res.json()["data"]
    assert len(rules) >= 1

    rule1 = rules[0]
    rule_id = rule1["id"]

    # 6. Verify rule can be edited
    update_res = client.put(
        f"/api/v1/policies/rules/{rule_id}",
        json={"name": "Verified Meal Limit", "verification_status": "MODIFIED"},
        headers=org_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["name"] == "Verified Meal Limit"

    # 7. Approve rules
    app_res = client.post(f"/api/v1/policies/rules/{rule_id}/approve?decision=APPROVED", headers=org_headers)
    assert app_res.status_code == 200
    assert app_res.json()["data"]["approval_status"] == "APPROVED"

    # 8. Activate policy version as official reference standard
    act_res = client.post(f"/api/v1/policies/versions/{version_id}/activate", headers=org_headers)
    assert act_res.status_code == 200
    assert act_res.json()["data"]["status"] == "ACTIVE"


def test_claim_evaluation_pass_and_violation(client: TestClient) -> None:
    """Verifies employee claim submission and deterministic policy evaluation against active approved rules."""
    admin_headers = get_authenticated_headers(client, role="ADMIN")
    user_headers = get_authenticated_headers(client, role="USER")

    # 1. Create Org and Policy
    org_slug = f"eval-corp-{uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/v1/organizations",
        json={"name": "Evaluation Corp", "slug": org_slug},
        headers=admin_headers,
    )
    assert res.status_code == 201
    org_id = res.json()["data"]["id"]
    org_headers = {**user_headers, "X-Organization-Id": org_id}
    admin_org_headers = {**admin_headers, "X-Organization-Id": org_id}

    # Upload standard policy with $50 meal limit
    policy_text = (
        "Expense Policy.\n"
        "Meal expenses are capped at $50.00 per meal.\n"
        "Original receipt is mandatory for all claims.\n"
        "Claims must be submitted within 30 days."
    )
    pdf_file = create_test_pdf_file(policy_text)
    upload_res = client.post(
        "/api/v1/documents",
        files={"file": ("Expense_Standard.pdf", pdf_file, "application/pdf")},
        headers=admin_org_headers,
    )
    doc_id = upload_res.json()["data"]["id"]

    pol_res = client.post(
        f"/api/v1/policies?document_id={doc_id}",
        json={"name": "Standard Expense Policy", "category": "EXPENSE"},
        headers=admin_org_headers,
    )
    policy_id = pol_res.json()["data"]["id"]

    # Get version and activate it
    detail_res = client.get(f"/api/v1/policies/{policy_id}", headers=admin_org_headers)
    version_id = detail_res.json()["data"]["versions"][0]["id"]

    client.post(f"/api/v1/policies/versions/{version_id}/extract", headers=admin_org_headers)
    act_res = client.post(f"/api/v1/policies/versions/{version_id}/activate", headers=admin_org_headers)
    assert act_res.status_code == 200

    # 2. Case A: Employee submits claim that violates meal limit ($85 > $50)
    claim_payload = {
        "claim_type": "EXPENSE",
        "title": "Client Business Lunch",
        "policy_id": policy_id,
        "expense_date": str(date.today()),
        "currency": "USD",
        "line_items": [
            {
                "category": "MEALS",
                "description": "Lunch with prospective partner",
                "amount": 85.0,
                "currency": "USD",
            }
        ],
        "document_ids": [],
    }

    claim_res = client.post("/api/v1/claims", json=claim_payload, headers=org_headers)
    assert claim_res.status_code == 201
    claim_data = claim_res.json()["data"]
    claim_id = claim_data["id"]

    # 3. Evaluate claim
    eval_res = client.post(f"/api/v1/claims/{claim_id}/evaluate", headers=org_headers)
    assert eval_res.status_code == 200
    evaluation = eval_res.json()["data"]

    # Expect VIOLATION outcome because $85 > $50 limit and missing receipt
    assert evaluation["evaluation_result"] in ("VIOLATION", "INSUFFICIENT_DATA")
    assert evaluation["violations_count"] >= 1
    assert any("exceeds approved policy limit" in f["description"] for f in evaluation["findings"])
    assert evaluation["review_task_id"] is not None

    # 4. Case B: Employee submits compliant claim ($40 <= $50) with attached receipt
    receipt_pdf = create_test_pdf_file("Receipt: Restaurant $40.00 Date: 2026-11-19")
    receipt_upload = client.post(
        "/api/v1/documents",
        files={"file": ("Lunch_Receipt.pdf", receipt_pdf, "application/pdf")},
        headers=org_headers,
    )
    receipt_doc_id = receipt_upload.json()["data"]["id"]

    comp_payload = {
        "claim_type": "EXPENSE",
        "title": "Subway Lunch",
        "policy_id": policy_id,
        "expense_date": str(date.today()),
        "currency": "USD",
        "line_items": [
            {
                "category": "MEALS",
                "description": "Standard working lunch",
                "amount": 40.0,
                "currency": "USD",
            }
        ],
        "document_ids": [receipt_doc_id],
    }

    comp_res = client.post("/api/v1/claims", json=comp_payload, headers=org_headers)
    assert comp_res.status_code == 201
    comp_claim_id = comp_res.json()["data"]["id"]

    eval_comp_res = client.post(f"/api/v1/claims/{comp_claim_id}/evaluate", headers=org_headers)
    assert eval_comp_res.status_code == 200
    comp_eval = eval_comp_res.json()["data"]

    # Meal limit is satisfied ($40 <= $50), so no meal limit violation finding
    assert not any("LIMIT_EXCEEDED" in f["finding_code"] for f in comp_eval["findings"])


def test_tenant_isolation_security_boundaries(client: TestClient) -> None:
    """Verifies that an employee in Org A cannot access claims or policies from Org B."""
    admin_headers = get_authenticated_headers(client, role="ADMIN")
    user_headers = get_authenticated_headers(client, role="USER")

    org_a = client.post("/api/v1/organizations", json={"name": "Org Alpha", "slug": f"alpha-{uuid.uuid4().hex[:6]}"}, headers=admin_headers).json()["data"]
    org_b = client.post("/api/v1/organizations", json={"name": "Org Beta", "slug": f"beta-{uuid.uuid4().hex[:6]}"}, headers=admin_headers).json()["data"]

    headers_org_a = {**admin_headers, "X-Organization-Id": org_a["id"]}
    headers_org_b = {**user_headers, "X-Organization-Id": org_b["id"]}

    # Create policy in Org A
    pol_a = client.post("/api/v1/policies", json={"name": "Secret Policy Alpha", "category": "EXPENSE"}, headers=headers_org_a).json()["data"]

    # User in Org B requests policy of Org A -> MUST return 404
    cross_res = client.get(f"/api/v1/policies/{pol_a['id']}", headers=headers_org_b)
    assert cross_res.status_code == 404
