"""Tests for analytics API endpoints."""
from datetime import date, timedelta


class TestAnalyticsAPI:
    """Test analytics API endpoints."""

    def test_get_portfolio_summary(self, client):
        """Test getting portfolio summary."""
        # Create diverse transactions
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today() - timedelta(days=2)),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.50,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today() - timedelta(days=1)),
                "isin": "US0378331005",
                "broker": "Broker",
                "fee": 2.00,
                "price_per_unit": 200.00,
                "units": 5.0,
                "transaction_type": "BUY"
            }
        )
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.50,
                "price_per_unit": 120.00,
                "units": 3.0,
                "transaction_type": "SELL"
            }
        )

        response = client.get("/api/v1/analytics/portfolio-summary")

        assert response.status_code == 200
        data = response.json()

        # Check all expected fields
        assert "total_invested" in data
        assert "total_withdrawn" in data
        assert "total_fees" in data
        assert "total_current_portfolio_invested_value" in data
        assert "total_profit_loss" in data
        assert "holdings" in data

        # Verify values make sense
        assert float(data["total_invested"]) > 0
        assert float(data["total_withdrawn"]) > 0
        assert float(data["total_fees"]) > 0
        assert float(data["total_current_portfolio_invested_value"]) == 0.0  # No position values added
        # P/L = 0 (current) + 360 (withdrawn) - 5.0 (fees) - 2000 (invested) = -1645.0
        assert float(data["total_profit_loss"]) < 0  # Should be negative
        assert len(data["holdings"]) == 2

    def test_get_portfolio_summary_empty(self, client):
        """Test portfolio summary with no transactions."""
        response = client.get("/api/v1/analytics/portfolio-summary")

        assert response.status_code == 200
        data = response.json()

        assert data["total_invested"] == "0"
        assert data["total_withdrawn"] == "0"
        assert data["total_fees"] == "0"
        assert data["total_current_portfolio_invested_value"] == "0"
        assert data["total_profit_loss"] == "0"
        assert data["holdings"] == []

    def test_get_portfolio_summary_with_position_values(self, client):
        """Test portfolio summary includes sum of position values."""
        # Create some transactions
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today() - timedelta(days=1)),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.50,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "US0378331005",
                "broker": "Broker",
                "fee": 2.00,
                "price_per_unit": 200.00,
                "units": 5.0,
                "transaction_type": "BUY"
            }
        )

        # Create position values
        client.post(
            "/api/v1/position-values",
            json={
                "isin": "IE00B4L5Y983",
                "current_value": 1100.00
            }
        )
        client.post(
            "/api/v1/position-values",
            json={
                "isin": "US0378331005",
                "current_value": 1050.00
            }
        )

        # Get portfolio summary
        response = client.get("/api/v1/analytics/portfolio-summary")

        assert response.status_code == 200
        data = response.json()

        # Verify position values are summed correctly
        assert float(data["total_current_portfolio_invested_value"]) == 2150.00
        assert float(data["total_invested"]) == 2000.00  # (100*10 + 200*5)
        assert float(data["total_fees"]) == 3.50  # (1.50 + 2.00)
        # P/L = 2150 (current) + 0 (withdrawn) - 3.50 (fees) - 2000 (invested) = 146.50
        assert float(data["total_profit_loss"]) == 146.50
        assert len(data["holdings"]) == 2
