"""Tests for API key middleware using API_KEY_DB_MAP."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class TestApiKeyDbMap:
    """Tests for the multi-key middleware using API_KEY_DB_MAP."""

    @patch("app.main._api_key_db_map", {"valid-key": "sqlite:///./test.db"})
    def test_valid_key_passes(self, client):
        """Valid key in the map passes through."""
        response = client.get(
            "/v1/transactions",
            headers={"X-API-Key": "valid-key"},
        )
        assert response.status_code == 200

    @patch("app.main._api_key_db_map", {"valid-key": "sqlite:///./test.db"})
    def test_invalid_key_rejected(self, client):
        """Key not in the map gets 401."""
        response = client.get(
            "/v1/transactions",
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or missing API key"

    @patch("app.main._api_key_db_map", {"valid-key": "sqlite:///./test.db"})
    def test_missing_key_rejected(self, client):
        """Request without key gets 401 when map is configured."""
        response = client.get("/v1/transactions")
        assert response.status_code == 401

    @patch("app.main._api_key_db_map", {"valid-key": "sqlite:///./test.db"})
    def test_health_bypasses_map(self, client):
        """Health endpoints bypass map auth."""
        for path in ["/health", "/v1/health", "/"]:
            response = client.get(path)
            assert response.status_code == 200, f"{path} should bypass auth"

    @patch("app.main._api_key_db_map", {"valid-key": "sqlite:///./test.db"})
    def test_options_bypasses_map(self, client):
        """OPTIONS requests bypass map auth."""
        response = client.options("/v1/transactions")
        assert response.status_code != 401

    def test_no_auth_when_map_empty(self, client):
        """When API_KEY_DB_MAP is empty, all requests pass through without auth."""
        response = client.get("/v1/transactions")
        assert response.status_code == 200
