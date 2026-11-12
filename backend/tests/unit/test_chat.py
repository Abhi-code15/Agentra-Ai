"""Unit tests for the AI Chatbot endpoint."""
import io
import uuid
from unittest.mock import patch
import pymupdf
import pytest
from fastapi.testclient import TestClient


def create_sample_pdf() -> io.BytesIO:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Department manager limit is 5000 INR. Senior VP approves over 10000 INR.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return io.BytesIO(pdf_bytes)


def test_chat_general_governance_assistant(client: TestClient) -> None:
    """Verifies that the chatbot responds to general compliance queries."""
    email = f"chat_user_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "full_name": "Chat User", "password": "Password123!"})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login_res.json()["data"]["access_token"]

    with patch("app.integrations.gemini.client.GeminiClient.chat_with_document") as mock_chat:
        mock_chat.return_value = "Manager approval is required for expenses up to 5,000 INR."

        res = client.post(
            "/api/v1/chat",
            json={
                "message": "What is the manager approval limit?",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert res.status_code == 200
        data = res.json()["data"]
        assert "5,000 INR" in data["reply"]
        assert len(data["suggested_questions"]) > 0


def test_chat_document_scoped_assistant(client: TestClient) -> None:
    """Verifies that the chatbot can be scoped to a specific document."""
    email = f"chat_doc_user_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "full_name": "Doc Chat User", "password": "Password123!"})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload document
    pdf_file = create_sample_pdf()
    upload_res = client.post(
        "/api/v1/documents",
        files={"file": ("Travel_Policy.pdf", pdf_file, "application/pdf")},
        headers=headers,
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["data"]["id"]

    with patch("app.integrations.gemini.client.GeminiClient.chat_with_document") as mock_chat:
        mock_chat.return_value = "According to Travel_Policy.pdf, Senior VP approval is required for claims above 10,000 INR."

        res = client.post(
            "/api/v1/chat",
            json={
                "message": "Who approves above 10,000?",
                "document_id": doc_id,
            },
            headers=headers,
        )

        assert res.status_code == 200
        data = res.json()["data"]
        assert data["document_id"] == doc_id
        assert "Senior VP" in data["reply"]
