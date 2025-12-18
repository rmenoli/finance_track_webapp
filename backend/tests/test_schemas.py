"""Tests for Pydantic schema validation."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.constants import TransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.schemas.position_value import PositionValueCreate


class TestTransactionSchemas:
    """Test transaction schema validation."""

    def test_transaction_create_valid(self):
        """Test creating a valid transaction schema."""
        transaction = TransactionCreate(
            date=date.today(),
            isin="IE00B4L5Y983",
            broker="Interactive Brokers",
            fee=Decimal("1.50"),
            price_per_unit=Decimal("450.25"),
            units=Decimal("10.0"),
            transaction_type=TransactionType.BUY
        )

        assert transaction.isin == "IE00B4L5Y983"
        assert transaction.broker == "Interactive Brokers"

    def test_transaction_create_isin_uppercase_conversion(self):
        """Test that ISIN is converted to uppercase."""
        transaction = TransactionCreate(
            date=date.today(),
            isin="ie00b4l5y983",  # lowercase
            broker="Broker",
            fee=Decimal("1.00"),
            price_per_unit=Decimal("100.00"),
            units=Decimal("10.0"),
            transaction_type=TransactionType.BUY
        )

        assert transaction.isin == "IE00B4L5Y983"  # Should be uppercase

    def test_transaction_create_invalid_isin_too_short(self):
        """Test that short ISIN is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                date=date.today(),
                isin="INVALID",  # Too short
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )

        assert "String should have at least 12 characters" in str(exc_info.value)

    def test_transaction_create_invalid_isin_format(self):
        """Test that invalid ISIN format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                date=date.today(),
                isin="1234567890AB",  # 12 chars but wrong format (should start with letters, not numbers)
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )

        assert "ISIN must be 12 characters" in str(exc_info.value)

    def test_transaction_create_future_date_rejected(self):
        """Test that future dates are rejected."""
        future_date = date.today() + timedelta(days=1)

        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                date=future_date,
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )

        assert "cannot be in the future" in str(exc_info.value)

    def test_transaction_create_today_date_accepted(self):
        """Test that today's date is accepted."""
        transaction = TransactionCreate(
            date=date.today(),
            isin="IE00B4L5Y983",
            broker="Broker",
            fee=Decimal("1.00"),
            price_per_unit=Decimal("100.00"),
            units=Decimal("10.0"),
            transaction_type=TransactionType.BUY
        )

        assert transaction.date == date.today()

    def test_transaction_create_past_date_accepted(self):
        """Test that past dates are accepted."""
        past_date = date.today() - timedelta(days=30)

        transaction = TransactionCreate(
            date=past_date,
            isin="IE00B4L5Y983",
            broker="Broker",
            fee=Decimal("1.00"),
            price_per_unit=Decimal("100.00"),
            units=Decimal("10.0"),
            transaction_type=TransactionType.BUY
        )

        assert transaction.date == past_date

    def test_transaction_create_negative_units_rejected(self):
        """Test that negative units are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("-10.0"),  # Negative
                transaction_type=TransactionType.BUY
            )

        assert "greater than 0" in str(exc_info.value)

    def test_transaction_create_zero_units_rejected(self):
        """Test that zero units are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("0.0"),  # Zero
                transaction_type=TransactionType.BUY
            )

        assert "greater than 0" in str(exc_info.value)

    def test_transaction_create_negative_price_rejected(self):
        """Test that negative price is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("-100.00"),  # Negative
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )

        assert "greater than 0" in str(exc_info.value)

    def test_transaction_create_zero_price_rejected(self):
        """Test that zero price is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("0.0"),  # Zero
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )

        assert "greater than 0" in str(exc_info.value)

    def test_transaction_create_negative_fee_rejected(self):
        """Test that negative fee is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("-1.00"),  # Negative
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )

        assert "greater than or equal to 0" in str(exc_info.value)

    def test_transaction_create_zero_fee_accepted(self):
        """Test that zero fee is accepted."""
        transaction = TransactionCreate(
            date=date.today(),
            isin="IE00B4L5Y983",
            broker="Broker",
            fee=Decimal("0.00"),  # Zero is OK for fees
            price_per_unit=Decimal("100.00"),
            units=Decimal("10.0"),
            transaction_type=TransactionType.BUY
        )

        assert transaction.fee == Decimal("0.00")

    def test_transaction_create_default_fee(self):
        """Test that fee defaults to 0.00 if not provided."""
        transaction = TransactionCreate(
            date=date.today(),
            isin="IE00B4L5Y983",
            broker="Broker",
            # fee not provided
            price_per_unit=Decimal("100.00"),
            units=Decimal("10.0"),
            transaction_type=TransactionType.BUY
        )

        assert transaction.fee == Decimal("0.00")

    def test_transaction_create_empty_broker_rejected(self):
        """Test that empty broker name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="",  # Empty
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )

        assert "at least 1 character" in str(exc_info.value)

    def test_transaction_update_partial_fields(self):
        """Test updating with only some fields."""
        update = TransactionUpdate(
            broker="New Broker",
            fee=Decimal("2.00")
        )

        assert update.broker == "New Broker"
        assert update.fee == Decimal("2.00")
        assert update.isin is None
        assert update.date is None

    def test_transaction_update_all_fields_optional(self):
        """Test that all fields in update are optional."""
        update = TransactionUpdate()

        assert update.broker is None
        assert update.fee is None
        assert update.isin is None

    def test_transaction_update_isin_validation(self):
        """Test that ISIN validation applies to updates."""
        with pytest.raises(ValidationError):
            TransactionUpdate(isin="INVALID")

    def test_transaction_update_isin_uppercase(self):
        """Test that ISIN is uppercased in updates."""
        update = TransactionUpdate(isin="ie00b4l5y983")
        assert update.isin == "IE00B4L5Y983"

    def test_transaction_update_future_date_rejected(self):
        """Test that future dates are rejected in updates."""
        future_date = date.today() + timedelta(days=1)

        with pytest.raises(ValidationError):
            TransactionUpdate(date=future_date)

    def test_transaction_update_negative_values_rejected(self):
        """Test that negative values are rejected in updates."""
        # Negative units
        with pytest.raises(ValidationError):
            TransactionUpdate(units=Decimal("-10.0"))

        # Negative price
        with pytest.raises(ValidationError):
            TransactionUpdate(price_per_unit=Decimal("-100.00"))

        # Negative fee
        with pytest.raises(ValidationError):
            TransactionUpdate(fee=Decimal("-1.00"))

    def test_transaction_type_enum(self):
        """Test transaction type enum values."""
        buy_transaction = TransactionCreate(
            date=date.today(),
            isin="IE00B4L5Y983",
            broker="Broker",
            fee=Decimal("1.00"),
            price_per_unit=Decimal("100.00"),
            units=Decimal("10.0"),
            transaction_type=TransactionType.BUY
        )

        sell_transaction = TransactionCreate(
            date=date.today(),
            isin="IE00B4L5Y983",
            broker="Broker",
            fee=Decimal("1.00"),
            price_per_unit=Decimal("100.00"),
            units=Decimal("10.0"),
            transaction_type=TransactionType.SELL
        )

        assert buy_transaction.transaction_type == TransactionType.BUY
        assert sell_transaction.transaction_type == TransactionType.SELL

    def test_valid_isin_formats(self):
        """Test various valid ISIN formats."""
        valid_isins = [
            "IE00B4L5Y983",  # Irish ISIN
            "US0378331005",  # US ISIN
            "GB0002374006",  # UK ISIN
            "DE0005140008",  # German ISIN
        ]

        for isin in valid_isins:
            transaction = TransactionCreate(
                date=date.today(),
                isin=isin,
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )
            assert transaction.isin == isin


class TestPositionValueSchemas:
    """Test position value schema validation."""

    def test_position_value_create_valid(self):
        """Test creating valid position value schema."""
        pv = PositionValueCreate(
            isin="IE00B4L5Y983",
            current_value=Decimal("5000.50")
        )

        assert pv.isin == "IE00B4L5Y983"
        assert pv.current_value == Decimal("5000.50")

    def test_position_value_create_negative_value(self):
        """Test that negative current_value is rejected."""
        with pytest.raises(ValidationError):
            PositionValueCreate(
                isin="IE00B4L5Y983",
                current_value=Decimal("-100.00")
            )

    def test_position_value_create_zero_value(self):
        """Test that zero current_value is rejected."""
        with pytest.raises(ValidationError):
            PositionValueCreate(
                isin="IE00B4L5Y983",
                current_value=Decimal("0.00")
            )

    def test_position_value_create_missing_fields(self):
        """Test that missing required fields are rejected."""
        # Missing current_value
        with pytest.raises(ValidationError):
            PositionValueCreate(isin="IE00B4L5Y983")

        # Missing isin
        with pytest.raises(ValidationError):
            PositionValueCreate(current_value=Decimal("1000.00"))
