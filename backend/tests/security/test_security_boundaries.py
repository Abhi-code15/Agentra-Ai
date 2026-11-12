"""Comprehensive security boundary tests verifying BOLA, RBAC, Token Replay, and Input Sanitization."""
import io
import uuid
import pytest
import pymupdf
from fastapi.testclient import TestClient


def create_minimal_pdf() -> io.BytesIO:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Security test corporate expense policy.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return io.BytesIO(pdf_bytes)


def test_broken_object_level_authorization_bola(client: TestClient) -> None:
    """Verifies that User B cannot access, delete, or trigger analysis on User A's documents."""
    # Register and login User A
    email_a = f"alice_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email_a, "full_name": "Alice Corp", "password": "Password123!"})
    res_a = client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
    token_a = res_a.json()["data"]["access_token"]

    # Register and login User B
    email_b = f"bob_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email_b, "full_name": "Bob Corp", "password": "Password123!"})
    res_b = client.post("/api/v1/auth/login", json={"email": email_b, "password": "Password123!"})
    token_b = res_b.json()["data"]["access_token"]

    # Alice uploads a document
    pdf_file = create_minimal_pdf()
    res_upload = client.post(
        "/api/v1/documents",
        files={"file": ("alice_policy.pdf", pdf_file, "application/pdf")},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_upload.status_code == 201
    doc_id = res_upload.json()["data"]["id"]

    # Bob attempts to read Alice's document -> Must fail with 404 (BOLA isolation)
    res_read = client.get(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_read.status_code == 404
    assert res_read.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"

    # Bob attempts to analyze Alice's document -> Must fail with 404
    res_analyze = client.post(f"/api/v1/documents/{doc_id}/analyze", headers={"Authorization": f"Bearer {token_b}"})
    assert res_analyze.status_code == 404
    assert res_analyze.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"

    # Bob attempts to delete Alice's document -> Must fail with 404
    res_delete = client.delete(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_delete.status_code == 404
    assert res_delete.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"

    # Alice can still access her document
    res_alice_read = client.get(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res_alice_read.status_code == 200


def test_rbac_user_cannot_access_reviewer_endpoints(client: TestClient) -> None:
    """Verifies that standard USER role cannot access REVIEWER-only endpoints."""
    email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "full_name": "Standard User", "password": "Password123!"})
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = res.json()["data"]["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Standard user attempts to view review tasks
    res_reviews = client.get("/api/v1/reviews", headers=headers)
    assert res_reviews.status_code == 403
    assert res_reviews.json()["error"]["code"] == "FORBIDDEN_INSUFFICIENT_ROLE"

    # Standard user attempts to submit a decision
    dummy_task_id = str(uuid.uuid4())
    res_decision = client.post(
        f"/api/v1/reviews/{dummy_task_id}/decision",
        json={"action": "APPROVED", "comments": "Self approving"},
        headers=headers,
    )
    assert res_decision.status_code == 403
    assert res_decision.json()["error"]["code"] == "FORBIDDEN_INSUFFICIENT_ROLE"


def test_token_tampering_and_forgery(client: TestClient) -> None:
    """Verifies rejection of forged, missing, or malformed authorization headers."""
    # 1. Missing Authorization header
    res_no_auth = client.get("/api/v1/documents")
    assert res_no_auth.status_code == 401
    assert res_no_auth.json()["error"]["code"] == "AUTH_TOKEN_MISSING"

    # 2. Tampered JWT token
    res_bad_jwt = client.get(
        "/api/v1/documents",
        headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.bogussignature"},
    )
    assert res_bad_jwt.status_code == 401
    assert res_bad_jwt.json()["error"]["code"] == "AUTH_TOKEN_INVALID"

    # 3. Non-bearer scheme (HTTPBearer treats this as missing credentials)
    res_bad_scheme = client.get(
        "/api/v1/documents",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert res_bad_scheme.status_code == 401
    assert res_bad_scheme.json()["error"]["code"] == "AUTH_TOKEN_MISSING"


def test_refresh_token_replay_attack_revokes_entire_family(client: TestClient) -> None:
    """Verifies that reusing an already rotated refresh token triggers family revocation."""
    email = f"replay_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "full_name": "Replay Tester", "password": "Password123!"})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    cookie_1 = login_res.cookies.get("refresh_token")
    assert cookie_1 is not None

    # Legitimate refresh 1: Cookie 1 exchanged for Cookie 2
    client.cookies.set("refresh_token", cookie_1)
    refresh_1 = client.post("/api/v1/auth/refresh")
    assert refresh_1.status_code == 200
    cookie_2 = refresh_1.cookies.get("refresh_token")
    assert cookie_2 is not None
    assert cookie_2 != cookie_1

    # Malicious replay: Attacker uses Cookie 1 again!
    client.cookies.set("refresh_token", cookie_1)
    replay_attack = client.post("/api/v1/auth/refresh")
    # Must fail with 401 and code AUTH_SESSION_REVOKED
    assert replay_attack.status_code == 401
    assert replay_attack.json()["error"]["code"] == "AUTH_SESSION_REVOKED"

    # Verify family revocation: The legitimate Cookie 2 must now ALSO be invalidated
    client.cookies.set("refresh_token", cookie_2)
    refresh_after_breach = client.post("/api/v1/auth/refresh")
    assert refresh_after_breach.status_code == 401
    assert refresh_after_breach.json()["error"]["code"] == "AUTH_SESSION_REVOKED"


def test_malicious_file_upload_safeguards(client: TestClient) -> None:
    """Verifies protection against path traversal filenames, unsupported types, and magic byte mismatch."""
    email = f"uploader_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "full_name": "Uploader", "password": "Password123!"})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Path traversal filename -> sanitized to safe basename and stored by random UUID
    pdf_file = create_minimal_pdf()
    res_traversal = client.post(
        "/api/v1/documents",
        files={"file": ("../../../../etc/passwd.pdf", pdf_file, "application/pdf")},
        headers=headers,
    )
    assert res_traversal.status_code == 201
    stored_name = res_traversal.json()["data"]["original_filename"]
    assert ".." not in stored_name
    assert "/" not in stored_name and "\\" not in stored_name
    assert stored_name == "passwd.pdf"

    # 2. Unsupported extension (executable with PE signature)
    res_exe = client.post(
        "/api/v1/documents",
        files={"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00test123"), "application/octet-stream")},
        headers=headers,
    )
    assert res_exe.status_code == 415
    assert res_exe.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"

    # 3. Magic byte mismatch (claimed PDF but contains plain text without %PDF header)
    fake_pdf = io.BytesIO(b"This is just plain text, not a real PDF document.")
    res_fake = client.post(
        "/api/v1/documents",
        files={"file": ("fake.pdf", fake_pdf, "application/pdf")},
        headers=headers,
    )
    assert res_fake.status_code == 415
    assert res_fake.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
