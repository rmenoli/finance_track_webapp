"""Tests for settings API endpoints."""

from decimal import Decimal

import pytest


class TestSettingsAPI:
    """Test settings API endpoints."""

    def test_get_exchange_rate_not_set_returns_default(self, client, db_session):
        """Test GET /settings/exchange-rate when not set returns default."""
        response = client.get("/api/v1/settings/exchange-rate")

        assert response.status_code == 200
        data = response.json()
        assert data["exchange_rate"] == "25.00"
        assert "updated_at" in data

    def test_update_exchange_rate(self, client, db_session):
        """Test POST /settings/exchange-rate with valid data."""
        response = client.post(
            "/api/v1/settings/exchange-rate",
            json={"exchange_rate": 24.50}
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["exchange_rate"]) == Decimal("24.50")
        assert "updated_at" in data

    def test_update_exchange_rate_invalid_negative(self, client, db_session):
        """Test POST /settings/exchange-rate with negative value."""
        response = client.post(
            "/api/v1/settings/exchange-rate",
            json={"exchange_rate": -1.0}
        )

        assert response.status_code == 422  # Validation error

    def test_update_exchange_rate_invalid_zero(self, client, db_session):
        """Test POST /settings/exchange-rate with zero value."""
        response = client.post(
            "/api/v1/settings/exchange-rate",
            json={"exchange_rate": 0.0}
        )

        assert response.status_code == 422  # Validation error

    def test_get_after_update(self, client, db_session):
        """Test GET returns updated value."""
        # Update
        client.post(
            "/api/v1/settings/exchange-rate",
            json={"exchange_rate": 26.75}
        )

        # Get
        response = client.get("/api/v1/settings/exchange-rate")

        assert response.status_code == 200
        data = response.json()
        assert data["exchange_rate"] == "26.75"
