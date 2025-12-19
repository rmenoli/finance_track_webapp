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
                transaction_type=TransactionType.BUY,
            ),
        )

        result = cost_basis_service.calculate_cost_basis(db_session, "IE00B4L5Y983")

        assert result is not None
        assert result.total_units == Decimal("10.0")
        assert result.total_cost_without_fees == Decimal("1000.00")
        assert result.total_gains_without_fees == Decimal("0")
        assert result.total_fees == Decimal("1.50")
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
                transaction_type=TransactionType.BUY,
            ),
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
                transaction_type=TransactionType.BUY,
            ),
        )

        result = cost_basis_service.calculate_cost_basis(db_session, "IE00B4L5Y983")

        assert result is not None
        assert result.total_units == Decimal("15.0")
        assert result.total_cost_without_fees == Decimal("1550.00")
        assert result.total_gains_without_fees == Decimal("0")
        assert result.total_fees == Decimal("3.00")
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
                transaction_type=TransactionType.BUY,
            ),
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
                transaction_type=TransactionType.SELL,
            ),
        )

        result = cost_basis_service.calculate_cost_basis(db_session, "IE00B4L5Y983")

        assert result is not None
        assert result.total_units == Decimal("7.0")
        assert result.total_cost_without_fees == Decimal("1000.00")
        assert result.total_gains_without_fees == Decimal("330.00")
        assert result.total_fees == Decimal("3.00")
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
                transaction_type=TransactionType.BUY,
            ),
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
                transaction_type=TransactionType.SELL,
            ),
        )

        result = cost_basis_service.calculate_cost_basis(db_session, "IE00B4L5Y983")

        assert result is not None
        assert result.total_units == Decimal("0")
        assert result.total_cost_without_fees == Decimal("1000.00")
        assert result.total_gains_without_fees == Decimal("1100.00")
        assert result.total_fees == Decimal("3.00")
        assert result.transactions_count == 2

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
                transaction_type=TransactionType.BUY,
            ),
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
                transaction_type=TransactionType.BUY,
            ),
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
                transaction_type=TransactionType.BUY,
            ),
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
                transaction_type=TransactionType.BUY,
            ),
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
                transaction_type=TransactionType.BUY,
            ),
        )

        holdings, closed_positions = cost_basis_service.calculate_current_holdings_and_closed_positions(
            db_session, {}
        )

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
                transaction_type=TransactionType.BUY,
            ),
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
                transaction_type=TransactionType.SELL,
            ),
        )

        holdings, closed_positions = cost_basis_service.calculate_current_holdings_and_closed_positions(
            db_session, {}
        )
        assert len(holdings) == 0
        assert len(closed_positions) == 1

        # Verify closed position details
        closed_pos = closed_positions[0]
        assert closed_pos.isin == "IE00B4L5Y983"
        assert closed_pos.total_units == Decimal("0")
        assert closed_pos.transactions_count == 2

    def test_closed_position_tracks_costs_and_gains(self, db_session):
        """Test that closed positions correctly track costs, gains, and fees."""
        # Buy 10 units at 100 with 1.50 fee
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=2),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY,
            ),
        )

        # Sell all 10 units at 120 with 2.00 fee
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("120.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.SELL,
            ),
        )

        holdings, closed_positions = cost_basis_service.calculate_current_holdings_and_closed_positions(
            db_session, {}
        )

        assert len(holdings) == 0
        assert len(closed_positions) == 1

        closed_pos = closed_positions[0]
        assert closed_pos.isin == "IE00B4L5Y983"
        assert closed_pos.total_units == Decimal("0")
        # Total cost: 10 * 100 = 1000
        assert closed_pos.total_cost_without_fees == Decimal("1000.00")
        # Total gains: 10 * 120 = 1200
        assert closed_pos.total_gains_without_fees == Decimal("1200.00")
        # Total fees: 1.50 + 2.00 = 3.50
        assert closed_pos.total_fees == Decimal("3.50")
        assert closed_pos.transactions_count == 2

    def test_multiple_closed_positions(self, db_session):
        """Test multiple closed positions are tracked correctly."""
        # First closed position: IE00B4L5Y983
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=3),
                isin="IE00B4L5Y983",
                broker="Broker A",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("50.00"),
                units=Decimal("20.0"),
                transaction_type=TransactionType.BUY,
            ),
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=1),
                isin="IE00B4L5Y983",
                broker="Broker A",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("60.00"),
                units=Decimal("20.0"),
                transaction_type=TransactionType.SELL,
            ),
        )

        # Second closed position: US0378331005
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=2),
                isin="US0378331005",
                broker="Broker B",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("15.0"),
                transaction_type=TransactionType.BUY,
            ),
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="US0378331005",
                broker="Broker B",
                fee=Decimal("2.50"),
                price_per_unit=Decimal("110.00"),
                units=Decimal("15.0"),
                transaction_type=TransactionType.SELL,
            ),
        )

        holdings, closed_positions = cost_basis_service.calculate_current_holdings_and_closed_positions(
            db_session, {}
        )

        assert len(holdings) == 0
        assert len(closed_positions) == 2

        # Verify ISINs are in closed positions
        closed_isins = [pos.isin for pos in closed_positions]
        assert "IE00B4L5Y983" in closed_isins
        assert "US0378331005" in closed_isins

        # Verify each has zero units
        for pos in closed_positions:
            assert pos.total_units == Decimal("0")
            assert pos.transactions_count == 2

    def test_mixed_holdings_and_closed_positions(self, db_session):
        """Test scenario with both open holdings and closed positions."""
        # Open position: IE00B4L5Y983 (buy 10, still holding)
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=5),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY,
            ),
        )

        # Closed position: US0378331005 (buy and sell all)
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=3),
                isin="US0378331005",
                broker="Broker",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("200.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY,
            ),
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=1),
                isin="US0378331005",
                broker="Broker",
                fee=Decimal("2.50"),
                price_per_unit=Decimal("220.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.SELL,
            ),
        )

        # Partially closed position: LU0274208692 (buy 20, sell 15, holding 5)
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=4),
                isin="LU0274208692",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("150.00"),
                units=Decimal("20.0"),
                transaction_type=TransactionType.BUY,
            ),
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=2),
                isin="LU0274208692",
                broker="Broker",
                fee=Decimal("1.75"),
                price_per_unit=Decimal("160.00"),
                units=Decimal("15.0"),
                transaction_type=TransactionType.SELL,
            ),
        )

        holdings, closed_positions = cost_basis_service.calculate_current_holdings_and_closed_positions(
            db_session, {}
        )

        # Verify counts
        assert len(holdings) == 2  # IE00B4L5Y983 and LU0274208692
        assert len(closed_positions) == 1  # US0378331005

        # Verify open holdings
        holding_isins = [h.isin for h in holdings]
        assert "IE00B4L5Y983" in holding_isins
        assert "LU0274208692" in holding_isins

        # Verify holdings have units > 0
        for holding in holdings:
            assert holding.total_units > Decimal("0")

        # Verify closed position
        assert closed_positions[0].isin == "US0378331005"
        assert closed_positions[0].total_units == Decimal("0")

    def test_closed_position_with_multiple_buys_and_sells(self, db_session):
        """Test closed position with multiple buy and sell transactions."""
        # Buy 10 units at different times
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=10),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY,
            ),
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=8),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("110.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY,
            ),
        )

        # Sell in two batches
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=5),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("120.00"),
                units=Decimal("3.0"),
                transaction_type=TransactionType.SELL,
            ),
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=1),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("125.00"),
                units=Decimal("7.0"),
                transaction_type=TransactionType.SELL,
            ),
        )

        holdings, closed_positions = cost_basis_service.calculate_current_holdings_and_closed_positions(
            db_session, {}
        )

        assert len(holdings) == 0
        assert len(closed_positions) == 1

        closed_pos = closed_positions[0]
        assert closed_pos.isin == "IE00B4L5Y983"
        assert closed_pos.total_units == Decimal("0")
        # Total cost: (5 * 100) + (5 * 110) = 1050
        assert closed_pos.total_cost_without_fees == Decimal("1050.00")
        # Total gains: (3 * 120) + (7 * 125) = 1235
        assert closed_pos.total_gains_without_fees == Decimal("1235.00")
        # Total fees: 1.00 + 1.00 + 1.50 + 2.00 = 5.50
        assert closed_pos.total_fees == Decimal("5.50")
        assert closed_pos.transactions_count == 4

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
                transaction_type=TransactionType.BUY,
            ),
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
                transaction_type=TransactionType.BUY,
            ),
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
                transaction_type=TransactionType.SELL,
            ),
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
        assert len(summary.closed_positions) == 0

    def test_get_portfolio_summary_with_closed_positions(self, db_session):
        """Test portfolio summary includes closed positions correctly."""
        # Open holding: IE00B4L5Y983
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=10),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY,
            ),
        )

        # Closed position: US0378331005
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=5),
                isin="US0378331005",
                broker="Broker",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("200.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY,
            ),
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=2),
                isin="US0378331005",
                broker="Broker",
                fee=Decimal("2.50"),
                price_per_unit=Decimal("220.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.SELL,
            ),
        )

        # Another closed position: LU0274208692
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=8),
                isin="LU0274208692",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("150.00"),
                units=Decimal("8.0"),
                transaction_type=TransactionType.BUY,
            ),
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=3),
                isin="LU0274208692",
                broker="Broker",
                fee=Decimal("1.75"),
                price_per_unit=Decimal("160.00"),
                units=Decimal("8.0"),
                transaction_type=TransactionType.SELL,
            ),
        )

        summary = cost_basis_service.get_portfolio_summary(db_session)

        # Verify holdings and closed positions counts
        assert len(summary.holdings) == 1  # IE00B4L5Y983
        assert len(summary.closed_positions) == 2  # US0378331005, LU0274208692

        # Verify total invested: (100*10) + (200*5) + (150*8) = 3200
        assert summary.total_invested == Decimal("3200.00")

        # Verify total withdrawn: (220*5) + (160*8) = 2380
        assert summary.total_withdrawn == Decimal("2380.00")

        # Verify total fees: 1.00 + 2.00 + 2.50 + 1.50 + 1.75 = 8.75
        assert summary.total_fees == Decimal("8.75")

        # Verify holdings
        assert summary.holdings[0].isin == "IE00B4L5Y983"
        assert summary.holdings[0].total_units == Decimal("10.0")

        # Verify closed positions
        closed_isins = [pos.isin for pos in summary.closed_positions]
        assert "US0378331005" in closed_isins
        assert "LU0274208692" in closed_isins

        for pos in summary.closed_positions:
            assert pos.total_units == Decimal("0")

    def test_pl_calculation_with_position_value(self, db_session):
        """Test P/L calculation when position value is available."""
        from app.services import position_value_service
        from app.schemas.position_value import PositionValueCreate

        # Create a buy transaction: 10 units at 100 with 1.50 fee
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=1),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY,
            ),
        )

        # Set current position value to 1200 (20% gain)
        position_value_service.upsert_position_value(
            db_session,
            PositionValueCreate(isin="IE00B4L5Y983", current_value=Decimal("1200.00")),
        )

        summary = cost_basis_service.get_portfolio_summary(db_session)

        assert len(summary.holdings) == 1
        holding = summary.holdings[0]

        # Verify P/L calculations
        assert holding.current_value == Decimal("1200.00")

        # P/L without fees: 1200 - 1000 = 200 (20%)
        assert holding.absolute_pl_without_fees == Decimal("200.00")
        assert holding.percentage_pl_without_fees == Decimal("20.00")

        # P/L with fees: 1200 - (1000 + 1.50) = 198.50 (19.82%)
        assert holding.absolute_pl_with_fees == Decimal("198.50")
        assert abs(holding.percentage_pl_with_fees - Decimal("19.82017982017982017982017982")) < Decimal(
            "0.01"
        )

    def test_pl_calculation_without_position_value(self, db_session):
        """Test P/L fields are None when position value is not available."""
        # Create a buy transaction without setting position value
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=1),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY,
            ),
        )

        summary = cost_basis_service.get_portfolio_summary(db_session)

        assert len(summary.holdings) == 1
        holding = summary.holdings[0]

        # Verify P/L fields are None
        assert holding.current_value is None
        assert holding.absolute_pl_without_fees is None
        assert holding.percentage_pl_without_fees is None
        assert holding.absolute_pl_with_fees is None
        assert holding.percentage_pl_with_fees is None

    def test_pl_calculation_negative_pl(self, db_session):
        """Test P/L calculation with negative P/L (loss)."""
        from app.services import position_value_service
        from app.schemas.position_value import PositionValueCreate

        # Create a buy transaction: 10 units at 100 with 2.00 fee
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=1),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY,
            ),
        )

        # Set current position value to 800 (20% loss)
        position_value_service.upsert_position_value(
            db_session,
            PositionValueCreate(isin="IE00B4L5Y983", current_value=Decimal("800.00")),
        )

        summary = cost_basis_service.get_portfolio_summary(db_session)

        holding = summary.holdings[0]

        # P/L without fees: 800 - 1000 = -200 (-20%)
        assert holding.absolute_pl_without_fees == Decimal("-200.00")
        assert holding.percentage_pl_without_fees == Decimal("-20.00")

        # P/L with fees: 800 - (1000 + 2.00) = -202 (-20.16%)
        assert holding.absolute_pl_with_fees == Decimal("-202.00")
        assert abs(holding.percentage_pl_with_fees - Decimal("-20.15968063872255489021956088")) < Decimal(
            "0.01"
        )

    def test_pl_calculation_with_partial_sell(self, db_session):
        """Test P/L calculation after partial sell."""
        from app.services import position_value_service
        from app.schemas.position_value import PositionValueCreate

        # Buy 20 units at 100 with 2.00 fee
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=2),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("20.0"),
                transaction_type=TransactionType.BUY,
            ),
        )

        # Sell 10 units at 120 with 1.50 fee
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=1),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("120.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.SELL,
            ),
        )

        # Set current position value for remaining 10 units to 1100
        position_value_service.upsert_position_value(
            db_session,
            PositionValueCreate(isin="IE00B4L5Y983", current_value=Decimal("1100.00")),
        )

        summary = cost_basis_service.get_portfolio_summary(db_session)

        holding = summary.holdings[0]

        # Remaining cost basis without fees: 2000 - 1200 = 800 (for 10 units)
        # P/L without fees: 1100 - 800 = 300
        assert holding.absolute_pl_without_fees == Decimal("300.00")
        assert holding.percentage_pl_without_fees == Decimal("37.5")

    def test_closed_position_pl_calculation(self, db_session):
        """Test P/L calculation for closed positions (fully sold)."""
        # Buy 10 units at 100 with 1.50 fee
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=2),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY,
            ),
        )

        # Sell all 10 units at 120 with 2.00 fee
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("120.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.SELL,
            ),
        )

        summary = cost_basis_service.get_portfolio_summary(db_session)

        assert len(summary.closed_positions) == 1
        closed_pos = summary.closed_positions[0]

        # Verify realized P/L
        # P/L without fees: 1200 - 1000 = 200 (20%)
        assert closed_pos.absolute_pl_without_fees == Decimal("200.00")
        assert closed_pos.percentage_pl_without_fees == Decimal("20.00")

        # P/L with fees: 200 - (1.50 + 2.00) = 196.50
        # Percentage: 196.50 / (1000 + 3.50) * 100 = 19.58%
        assert closed_pos.absolute_pl_with_fees == Decimal("196.50")
        assert abs(closed_pos.percentage_pl_with_fees - Decimal("19.58")) < Decimal("0.01")

        # Current value should be 0 for closed position
        assert closed_pos.current_value == Decimal("0")

    def test_multiple_holdings_with_mixed_position_values(self, db_session):
        """Test P/L calculation with multiple holdings, some with position values."""
        from app.services import position_value_service
        from app.schemas.position_value import PositionValueCreate

        # Holding 1: With position value
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=1),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY,
            ),
        )
        position_value_service.upsert_position_value(
            db_session,
            PositionValueCreate(isin="IE00B4L5Y983", current_value=Decimal("1100.00")),
        )

        # Holding 2: Without position value
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today() - timedelta(days=1),
                isin="US0378331005",
                broker="Broker",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("200.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY,
            ),
        )

        summary = cost_basis_service.get_portfolio_summary(db_session)

        assert len(summary.holdings) == 2

        # Find each holding
        holding_with_value = next(h for h in summary.holdings if h.isin == "IE00B4L5Y983")
        holding_without_value = next(h for h in summary.holdings if h.isin == "US0378331005")

        # Verify holding with position value has P/L
        assert holding_with_value.current_value == Decimal("1100.00")
        assert holding_with_value.absolute_pl_without_fees == Decimal("100.00")
        assert holding_with_value.percentage_pl_without_fees == Decimal("10.00")

        # Verify holding without position value has None for P/L
        assert holding_without_value.current_value is None
        assert holding_without_value.absolute_pl_without_fees is None
        assert holding_without_value.percentage_pl_without_fees is None
