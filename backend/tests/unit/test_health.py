"""Unit tests for system health and readiness probes."""
from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Verifies that the /health endpoint returns healthy status and 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "agentra-api"


def test_readiness_check(client: TestClient) -> None:
    """Verifies that the /ready endpoint checks database and storage availability."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] == "connected"
    assert data["checks"]["storage"] == "writable"


def test_correlation_id_middleware(client: TestClient) -> None:
    """Verifies that incoming and outgoing correlation IDs are preserved."""
    custom_id = "test-correlation-id-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id
    assert "X-Process-Time-Ms" in response.headers
