"""Integration tests for document upload, listing, extraction inspection, and BOLA defense."""
import io
import uuid
import pytest
import pymupdf
from fastapi.testclient import TestClient


def create_test_pdf_file(text: str = "Test Policy") -> io.BytesIO:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return io.BytesIO(pdf_bytes)


def test_document_lifecycle_and_bola_isolation(client: TestClient) -> None:
    """Verifies document upload, extraction, listing, deletion, and BOLA ownership isolation."""
    # 1. Register and Login User A
    user_a_email = f"user_a_{uuid.uuid4().hex[:8]}@corp.com"
    client.post("/api/v1/auth/register", json={"email": user_a_email, "full_name": "User A", "password": "Password123!"})
    login_a = client.post("/api/v1/auth/login", json={"email": user_a_email, "password": "Password123!"})
    token_a = login_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register and Login User B
    user_b_email = f"user_b_{uuid.uuid4().hex[:8]}@corp.com"
    client.post("/api/v1/auth/register", json={"email": user_b_email, "full_name": "User B", "password": "Password123!"})
    login_b = client.post("/api/v1/auth/login", json={"email": user_b_email, "password": "Password123!"})
    token_b = login_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A Uploads a Valid Expense Policy PDF
    policy_content = (
        "Expense Reimbursement Policy 2026.\n"
        "1. Department Manager approval limit: INR 5,000.\n"
        "2. Finance approval limit: INR 10,000.\n"
        "3. Valid itemized tax invoice mandatory for all claims within 30 days."
    )
    pdf_file = create_test_pdf_file(policy_content)
    upload_res = client.post(
        "/api/v1/documents",
        files={"file": ("Expense_Policy_2026.pdf", pdf_file, "application/pdf")},
        headers=headers_a,
    )
    assert upload_res.status_code == 201
    upload_data = upload_res.json()["data"]
    doc_id = upload_data["id"]
    assert upload_data["original_filename"] == "Expense_Policy_2026.pdf"
    assert upload_data["document_status"] == "READY_FOR_ANALYSIS"
    assert upload_data["page_count"] == 1

    # 4. User A Lists Documents -> 1 document returned
    list_res = client.get("/api/v1/documents", headers=headers_a)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["pagination"]["total_records"] == 1
    assert list_data["data"][0]["id"] == doc_id

    # 5. User A Inspects Document Detail
    detail_res = client.get(f"/api/v1/documents/{doc_id}", headers=headers_a)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()["data"]
    assert detail_data["id"] == doc_id
    assert detail_data["extraction"] is not None
    assert detail_data["extraction"]["extraction_status"] == "COMPLETED"

    # 6. BOLA Check: User B attempts to access User A's document -> 404 Not Found
    bola_get = client.get(f"/api/v1/documents/{doc_id}", headers=headers_b)
    assert bola_get.status_code == 404
    assert bola_get.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"

    # 7. BOLA Check: User B attempts to delete User A's document -> 404 Not Found
    bola_delete = client.delete(f"/api/v1/documents/{doc_id}", headers=headers_b)
    assert bola_delete.status_code == 404

    # 8. User B Lists Documents -> 0 documents returned
    list_b_res = client.get("/api/v1/documents", headers=headers_b)
    assert list_b_res.status_code == 200
    assert list_b_res.json()["pagination"]["total_records"] == 0

    # 9. User A Deletes Document -> 200 OK
    delete_res = client.delete(f"/api/v1/documents/{doc_id}", headers=headers_a)
    assert delete_res.status_code == 200

    # 10. User A attempts to access soft-deleted document -> 404 Not Found
    post_delete_res = client.get(f"/api/v1/documents/{doc_id}", headers=headers_a)
    assert post_delete_res.status_code == 404
