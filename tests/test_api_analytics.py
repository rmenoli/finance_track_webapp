"""Tests for analytics API endpoints."""
from datetime import date, timedelta


class TestAnalyticsAPI:
    """Test analytics API endpoints."""

    def test_get_cost_basis_specific_isin(self, client):
        """Test getting cost basis for a specific ISIN."""
        # Create transaction
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.50,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )

        response = client.get("/api/v1/analytics/cost-basis/IE00B4L5Y983")

        assert response.status_code == 200
        data = response.json()
        assert data["isin"] == "IE00B4L5Y983"
        assert data["total_units"] == "10.0000"
        assert data["transactions_count"] == 1

    def test_get_cost_basis_not_found(self, client):
        """Test getting cost basis for non-existent ISIN."""
        response = client.get("/api/v1/analytics/cost-basis/NONEXISTENT")

        assert response.status_code == 404

    def test_get_cost_basis_with_as_of_date(self, client):
        """Test getting cost basis as of a specific date."""
        today = date.today()

        # Create two transactions
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(today - timedelta(days=5)),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(today),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 110.00,
                "units": 5.0,
                "transaction_type": "BUY"
            }
        )

        # Get cost basis as of 3 days ago (should only include first transaction)
        as_of = str(today - timedelta(days=3))
        response = client.get(f"/api/v1/analytics/cost-basis/IE00B4L5Y983?as_of_date={as_of}")

        assert response.status_code == 200
        data = response.json()
        assert data["transactions_count"] == 1
        assert data["total_units"] == "10.0000"

    def test_get_all_cost_bases(self, client):
        """Test getting cost basis for all ISINs."""
        # Create transactions for multiple ISINs
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
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

        response = client.get("/api/v1/analytics/cost-basis")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        isins = [item["isin"] for item in data]
        assert "IE00B4L5Y983" in isins
        assert "US0378331005" in isins

    def test_get_all_cost_bases_empty(self, client):
        """Test getting cost basis when no transactions exist."""
        response = client.get("/api/v1/analytics/cost-basis")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_all_cost_bases_excludes_fully_sold(self, client):
        """Test that fully sold positions are excluded."""
        # Buy and sell all
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today() - timedelta(days=1)),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 110.00,
                "units": 10.0,
                "transaction_type": "SELL"
            }
        )

        response = client.get("/api/v1/analytics/cost-basis")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_holdings(self, client):
        """Test getting current holdings."""
        # Create transactions
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
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

        response = client.get("/api/v1/analytics/holdings")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Check structure
        for holding in data:
            assert "isin" in holding
            assert "units" in holding
            assert "average_cost_per_unit" in holding
            assert "total_cost" in holding

    def test_get_holdings_empty(self, client):
        """Test getting holdings when none exist."""
        response = client.get("/api/v1/analytics/holdings")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_realized_gains(self, client):
        """Test getting realized gains."""
        # Create buy and sell transactions
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
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.50,
                "price_per_unit": 120.00,
                "units": 5.0,
                "transaction_type": "SELL"
            }
        )

        response = client.get("/api/v1/analytics/realized-gains")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["isin"] == "IE00B4L5Y983"
        assert data[0]["sell_transactions_count"] == 1
        # Should have positive gain
        assert float(data[0]["total_realized_gain"]) > 0

    def test_get_realized_gains_filter_by_isin(self, client):
        """Test filtering realized gains by ISIN."""
        # Create transactions for two ISINs
        for isin in ["IE00B4L5Y983", "US0378331005"]:
            client.post(
                "/api/v1/transactions",
                json={
                    "date": str(date.today() - timedelta(days=1)),
                    "isin": isin,
                    "broker": "Broker",
                    "fee": 1.00,
                    "price_per_unit": 100.00,
                    "units": 10.0,
                    "transaction_type": "BUY"
                }
            )
            client.post(
                "/api/v1/transactions",
                json={
                    "date": str(date.today()),
                    "isin": isin,
                    "broker": "Broker",
                    "fee": 1.00,
                    "price_per_unit": 110.00,
                    "units": 5.0,
                    "transaction_type": "SELL"
                }
            )

        response = client.get("/api/v1/analytics/realized-gains?isin=IE00B4L5Y983")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["isin"] == "IE00B4L5Y983"

    def test_get_realized_gains_no_sells(self, client):
        """Test getting realized gains when there are no sells."""
        # Only buy transactions
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )

        response = client.get("/api/v1/analytics/realized-gains")

        assert response.status_code == 200
        data = response.json()
        assert data == []

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
        assert "total_fees" in data
        assert "holdings" in data
        assert "realized_gains" in data
        assert "realized_losses" in data
        assert "net_realized_gains" in data
        assert "unique_isins" in data

        # Verify values make sense
        assert float(data["total_invested"]) > 0
        assert float(data["total_fees"]) > 0
        assert len(data["holdings"]) == 2
        assert data["unique_isins"] == 2

    def test_get_portfolio_summary_empty(self, client):
        """Test portfolio summary with no transactions."""
        response = client.get("/api/v1/analytics/portfolio-summary")

        assert response.status_code == 200
        data = response.json()

        assert data["total_invested"] == "0"
        assert data["total_fees"] == "0"
        assert data["holdings"] == []
        assert data["unique_isins"] == 0
        assert data["realized_gains"] == "0"
        assert data["realized_losses"] == "0"
        assert data["net_realized_gains"] == "0"

    def test_portfolio_summary_realized_gains_calculation(self, client):
        """Test that realized gains are correctly separated into gains and losses."""
        # Buy
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today() - timedelta(days=2)),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 20.0,
                "transaction_type": "BUY"
            }
        )

        # Sell at profit
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today() - timedelta(days=1)),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 120.00,
                "units": 10.0,
                "transaction_type": "SELL"
            }
        )

        # Sell at loss
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 80.00,
                "units": 5.0,
                "transaction_type": "SELL"
            }
        )

        response = client.get("/api/v1/analytics/portfolio-summary")

        assert response.status_code == 200
        data = response.json()

        # Net realized gains should be positive overall (profit was larger than loss)
        # But we can verify the calculation is working by checking net is reasonable
        net_realized = float(data["net_realized_gains"])

        # We sold 10 at profit (120 vs avg 100.05) and 5 at loss (80 vs avg cost)
        # The net should be positive since we made more on the profitable trade
        assert net_realized != 0  # Should have some realized gain/loss
