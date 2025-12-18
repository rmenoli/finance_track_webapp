"""Tests for cost basis service."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.constants import TransactionType
from app.schemas.transaction import TransactionCreate
from app.services import cost_basis_service, transaction_service


class TestCostBasisService:
    """Test cost basis calculations."""

    def test_calculate_cost_basis_single_buy(self, db_session):
        """Test cost basis for a single buy transaction."""
        # Create a buy transaction
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )
        )

        result = cost_basis_service.calculate_cost_basis(db_session, "IE00B4L5Y983")

        assert result is not None
        assert result.total_units == Decimal("10.0")
        # Total cost = (100 * 10) + 1.50 = 1001.50
        assert result.total_cost == Decimal("1001.50")
        assert result.transactions_count == 1

    def test_calculate_cost_basis_multiple_buys(self, db_session):
        """Test cost basis with multiple buy transactions at different prices."""
        # First buy: 10 units at $100
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=2),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )
        )

        # Second buy: 5 units at $110
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("110.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )

        result = cost_basis_service.calculate_cost_basis(db_session, "IE00B4L5Y983")

        assert result is not None
        assert result.total_units == Decimal("15.0")
        # Total cost = (100*10 + 1.50) + (110*5 + 1.50) = 1001.50 + 551.50 = 1553.00
        assert result.total_cost == Decimal("1553.00")
        assert result.transactions_count == 2

    def test_calculate_cost_basis_with_sell(self, db_session):
        """Test cost basis after a sell transaction."""
        # Buy 10 units at $100
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=2),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )
        )

        # Sell 3 units at $110
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("110.00"),
                units=Decimal("3.0"),
                transaction_type=TransactionType.SELL
            )
        )

        result = cost_basis_service.calculate_cost_basis(db_session, "IE00B4L5Y983")

        assert result is not None
        # Should have 7 units remaining (10 - 3)
        assert result.total_units == Decimal("7.0")
        # Original cost: 1001.50
        # Proportion sold: 3/10 = 0.3
        # Cost removed: 1001.50 * 0.3 = 300.45
        # Remaining cost: 1001.50 - 300.45 = 701.05
        assert result.total_cost == Decimal("701.05")
        assert result.transactions_count == 2

    def test_calculate_cost_basis_sell_all(self, db_session):
        """Test cost basis when all units are sold."""
        # Buy 10 units
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=2),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )
        )

        # Sell all 10 units
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("110.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.SELL
            )
        )

        result = cost_basis_service.calculate_cost_basis(db_session, "IE00B4L5Y983")

        assert result is not None
        assert result.total_units == Decimal("0")
        assert result.total_cost == Decimal("0")

    def test_calculate_cost_basis_no_transactions(self, db_session):
        """Test cost basis for non-existent ISIN."""
        result = cost_basis_service.calculate_cost_basis(db_session, "NONEXISTENT")
        assert result is None

    def test_calculate_cost_basis_case_insensitive(self, db_session):
        """Test that ISIN lookup is case insensitive."""
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )
        )

        # Query with lowercase
        result = cost_basis_service.calculate_cost_basis(db_session, "ie00b4l5y983")
        assert result is not None
        assert result.isin == "IE00B4L5Y983"

    def test_calculate_cost_basis_as_of_date(self, db_session):
        """Test cost basis calculation as of a specific date."""
        today = date.today()

        # Buy on day 1
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=today - timedelta(days=5),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )
        )

        # Buy on day 3
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=today - timedelta(days=3),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("110.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )

        # Calculate as of day 2 (should only include first transaction)
        result = cost_basis_service.calculate_cost_basis(
            db_session, "IE00B4L5Y983", as_of_date=today - timedelta(days=4)
        )

        assert result is not None
        assert result.total_units == Decimal("10.0")
        assert result.transactions_count == 1

    def test_calculate_current_holdings(self, db_session):
        """Test calculating current holdings for all ISINs."""
        # Create transactions for multiple ISINs
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="US0378331005",
                broker="Broker",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("200.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )

        holdings = cost_basis_service.calculate_current_holdings(db_session)

        assert len(holdings) == 2
        isins = [h.isin for h in holdings]
        assert "IE00B4L5Y983" in isins
        assert "US0378331005" in isins

    def test_calculate_current_holdings_excludes_fully_sold(self, db_session):
        """Test that fully sold positions are excluded from holdings."""
        # Buy and sell all
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=1),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("110.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.SELL
            )
        )

        holdings = cost_basis_service.calculate_current_holdings(db_session)
        assert len(holdings) == 0

    def test_get_portfolio_summary(self, db_session):
        """Test getting complete portfolio summary."""
        # Create buy transactions
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=2),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=1),
                isin="US0378331005",
                broker="Broker",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("200.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )

        # Create sell transaction
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("120.00"),
                units=Decimal("3.0"),
                transaction_type=TransactionType.SELL
            )
        )

        summary = cost_basis_service.get_portfolio_summary(db_session)

        # Total invested: (100*10) + (200*5) = 2000
        assert summary.total_invested == Decimal("2000.00")

        # Total fees: 1.50 + 2.00 + 1.50 = 5.00
        assert summary.total_fees == Decimal("5.00")

        # Should have 2 holdings (both ISINs still have positions)
        assert len(summary.holdings) == 2

    def test_get_portfolio_summary_empty(self, db_session):
        """Test portfolio summary with no transactions."""
        summary = cost_basis_service.get_portfolio_summary(db_session)

        assert summary.total_invested == 0
        assert summary.total_fees == 0
        assert len(summary.holdings) == 0
