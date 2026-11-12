"""Integration tests for user registration, authentication, token rotation, and logout."""
import uuid
import pytest
from fastapi.testclient import TestClient


def test_user_registration_and_duplicate_handling(client: TestClient) -> None:
    """Verifies that user registration succeeds and duplicate emails are rejected."""
    email = f"user_{uuid.uuid4().hex[:8]}@enterprise.com"
    payload = {
        "email": email,
        "full_name": "Priya Sharma",
        "password": "StrongPassword!2026",
        "role": "USER",
    }

    # First registration -> 201 Created
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == email
    assert data["data"]["full_name"] == "Priya Sharma"
    assert data["data"]["role"] == "USER"
    assert "id" in data["data"]

    # Duplicate registration -> 409 Conflict
    dup_response = client.post("/api/v1/auth/register", json=payload)
    assert dup_response.status_code == 409
    dup_data = dup_response.json()
    assert dup_data["success"] is False
    assert dup_data["error"]["code"] == "AUTH_EMAIL_EXISTS"


def test_login_and_token_issuance(client: TestClient) -> None:
    """Verifies user login with valid credentials returns JWT and sets refresh cookie."""
    email = f"login_{uuid.uuid4().hex[:8]}@enterprise.com"
    password = "CorrectPassword123!"

    # Register user
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": password, "role": "USER"},
    )

    # Valid Login
    login_response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["success"] is True
    assert "access_token" in login_data["data"]
    assert login_data["data"]["token_type"] == "Bearer"
    assert "refresh_token" in login_response.cookies

    # Invalid Login (wrong password)
    bad_login = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword!"})
    assert bad_login.status_code == 401
    assert bad_login.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"


def test_get_current_user_profile(client: TestClient) -> None:
    """Verifies that /auth/me returns current user profile when authenticated."""
    email = f"profile_{uuid.uuid4().hex[:8]}@enterprise.com"
    password = "CorrectPassword123!"

    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Profile User", "password": password, "role": "REVIEWER"},
    )

    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    access_token = login_res.json()["data"]["access_token"]

    # Call /auth/me with valid Bearer token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["success"] is True
    assert me_data["data"]["email"] == email
    assert me_data["data"]["role"] == "REVIEWER"

    # Call /auth/me without token -> 401
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401
    assert unauth_res.json()["error"]["code"] == "AUTH_TOKEN_MISSING"


def test_refresh_token_rotation_and_replay_protection(client: TestClient) -> None:
    """Verifies that refresh token rotation issues fresh tokens and revokes old ones."""
    email = f"refresh_{uuid.uuid4().hex[:8]}@enterprise.com"
    password = "CorrectPassword123!"

    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Rotation User", "password": password, "role": "USER"},
    )

    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    initial_refresh_cookie = login_res.cookies.get("refresh_token")
    assert initial_refresh_cookie is not None

    # First Refresh -> 200 OK and rotates cookie
    client.cookies.set("refresh_token", initial_refresh_cookie)
    refresh_res = client.post("/api/v1/auth/refresh")
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()["data"]

    new_refresh_cookie = refresh_res.cookies.get("refresh_token")
    assert new_refresh_cookie is not None
    assert new_refresh_cookie != initial_refresh_cookie

    # Replay Attack: presenting old already-rotated refresh token -> 401 Revoked
    client.cookies.set("refresh_token", initial_refresh_cookie)
    replay_res = client.post("/api/v1/auth/refresh")
    assert replay_res.status_code == 401
    assert replay_res.json()["error"]["code"] == "AUTH_SESSION_REVOKED"


def test_logout_session_invalidation(client: TestClient) -> None:
    """Verifies that logging out revokes the refresh session and deletes cookie."""
    email = f"logout_{uuid.uuid4().hex[:8]}@enterprise.com"
    password = "CorrectPassword123!"

    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Logout User", "password": password, "role": "USER"},
    )

    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    refresh_cookie = login_res.cookies.get("refresh_token")

    # Logout
    client.cookies.set("refresh_token", refresh_cookie)
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200

    # Attempt to refresh with logged-out session -> 401
    client.cookies.set("refresh_token", refresh_cookie)
    post_logout_res = client.post("/api/v1/auth/refresh")
    assert post_logout_res.status_code == 401
