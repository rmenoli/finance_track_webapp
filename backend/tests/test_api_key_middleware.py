"""Tests for API key middleware."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


@patch("app.main.settings")
def test_no_auth_when_api_key_empty(mock_settings, client):
    """When api_key is empty, all requests pass through without auth."""
    mock_settings.api_key = ""
    mock_settings.api_v1_prefix = "/v1"
    mock_settings.cors_origins_list = ["http://localhost:3000"]
    response = client.get("/v1/transactions")
    assert response.status_code == 200


@patch("app.main.settings")
def test_reject_request_without_key(mock_settings, client):
    """When api_key is set, requests without key get 401."""
    mock_settings.api_key = "test-secret-key"
    mock_settings.api_v1_prefix = "/v1"
    mock_settings.cors_origins_list = ["http://localhost:3000"]
    response = client.get("/v1/transactions")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


@patch("app.main.settings")
def test_reject_request_with_wrong_key(mock_settings, client):
    """When api_key is set, requests with wrong key get 401."""
    mock_settings.api_key = "test-secret-key"
    mock_settings.api_v1_prefix = "/v1"
    mock_settings.cors_origins_list = ["http://localhost:3000"]
    response = client.get(
        "/v1/transactions",
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


@patch("app.main.settings")
def test_accept_request_with_correct_key(mock_settings, client):
    """When api_key is set, requests with correct key pass through."""
    mock_settings.api_key = "test-secret-key"
    mock_settings.api_v1_prefix = "/v1"
    mock_settings.cors_origins_list = ["http://localhost:3000"]
    response = client.get(
        "/v1/transactions",
        headers={"X-API-Key": "test-secret-key"},
    )
    assert response.status_code == 200


@patch("app.main.settings")
def test_health_endpoint_bypasses_key(mock_settings, client):
    """Health endpoints are accessible without API key."""
    mock_settings.api_key = "test-secret-key"
    mock_settings.api_v1_prefix = "/v1"
    mock_settings.cors_origins_list = ["http://localhost:3000"]
    for path in ["/health", "/v1/health"]:
        response = client.get(path)
        assert response.status_code == 200, f"Health endpoint {path} should be open"


@patch("app.main.settings")
def test_root_endpoint_bypasses_key(mock_settings, client):
    """Root endpoint is accessible without API key."""
    mock_settings.api_key = "test-secret-key"
    mock_settings.api_v1_prefix = "/v1"
    mock_settings.cors_origins_list = ["http://localhost:3000"]
    response = client.get("/")
    assert response.status_code == 200


@patch("app.main.settings")
def test_options_request_bypasses_key(mock_settings, client):
    """OPTIONS requests bypass key check (CORS preflight)."""
    mock_settings.api_key = "test-secret-key"
    mock_settings.api_v1_prefix = "/v1"
    mock_settings.cors_origins_list = ["http://localhost:3000"]
    response = client.options("/v1/transactions")
    assert response.status_code != 401
