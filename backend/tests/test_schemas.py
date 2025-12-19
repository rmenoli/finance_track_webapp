"""Tests for Pydantic schema validation."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.constants import AssetType, Currency, ISINType, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.schemas.position_value import PositionValueCreate
from app.schemas.isin_metadata import ISINMetadataCreate, ISINMetadataUpdate
from app.schemas.other_asset import OtherAssetCreate


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


class TestISINMetadataSchemas:
    """Test ISIN metadata schema validation."""

    def test_isin_metadata_create_valid(self):
        """Test creating valid ISIN metadata schema."""
        metadata = ISINMetadataCreate(
            isin="IE00B4L5Y983",
            name="iShares Core MSCI Emerging Markets ETF",
            type=ISINType.STOCK
        )

        assert metadata.isin == "IE00B4L5Y983"
        assert metadata.name == "iShares Core MSCI Emerging Markets ETF"
        assert metadata.type == ISINType.STOCK

    def test_isin_metadata_create_isin_uppercase_conversion(self):
        """Test that ISIN is converted to uppercase."""
        metadata = ISINMetadataCreate(
            isin="ie00b4l5y983",  # lowercase
            name="Test ETF",
            type=ISINType.STOCK
        )

        assert metadata.isin == "IE00B4L5Y983"  # Should be uppercase

    def test_isin_metadata_create_invalid_isin_format(self):
        """Test that invalid ISIN format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ISINMetadataCreate(
                isin="1234567890AB",  # Wrong format (starts with digits)
                name="Test ETF",
                type=ISINType.STOCK
            )

        assert "ISIN must be 12 characters" in str(exc_info.value)

    def test_isin_metadata_create_name_strip_whitespace(self):
        """Test that name whitespace is stripped."""
        metadata = ISINMetadataCreate(
            isin="IE00B4L5Y983",
            name="  Test ETF  ",  # Leading/trailing whitespace
            type=ISINType.STOCK
        )

        assert metadata.name == "Test ETF"  # Whitespace should be stripped

    def test_isin_metadata_create_empty_name_rejected(self):
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError):
            ISINMetadataCreate(
                isin="IE00B4L5Y983",
                name="",
                type=ISINType.STOCK
            )

    def test_isin_metadata_create_invalid_type(self):
        """Test that invalid type is rejected."""
        with pytest.raises(ValidationError):
            ISINMetadataCreate(
                isin="IE00B4L5Y983",
                name="Test ETF",
                type="INVALID_TYPE"  # Not a valid ISINType
            )

    def test_isin_metadata_create_all_types(self):
        """Test all valid ISIN types."""
        for isin_type in [ISINType.STOCK, ISINType.BOND, ISINType.REAL_ASSET]:
            metadata = ISINMetadataCreate(
                isin="IE00B4L5Y983",
                name="Test Asset",
                type=isin_type
            )
            assert metadata.type == isin_type

    def test_isin_metadata_create_missing_fields(self):
        """Test that missing required fields are rejected."""
        # Missing name
        with pytest.raises(ValidationError):
            ISINMetadataCreate(isin="IE00B4L5Y983", type=ISINType.STOCK)

        # Missing type
        with pytest.raises(ValidationError):
            ISINMetadataCreate(isin="IE00B4L5Y983", name="Test ETF")

        # Missing isin
        with pytest.raises(ValidationError):
            ISINMetadataCreate(name="Test ETF", type=ISINType.STOCK)

    def test_isin_metadata_update_partial_fields(self):
        """Test updating with only some fields."""
        # Update only name
        update = ISINMetadataUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.type is None

        # Update only type
        update2 = ISINMetadataUpdate(type=ISINType.BOND)
        assert update2.name is None
        assert update2.type == ISINType.BOND

    def test_isin_metadata_update_all_fields_optional(self):
        """Test that all fields in update are optional."""
        update = ISINMetadataUpdate()
        assert update.name is None
        assert update.type is None

    def test_isin_metadata_update_name_strip_whitespace(self):
        """Test that name whitespace is stripped in updates."""
        update = ISINMetadataUpdate(name="  Updated Name  ")
        assert update.name == "Updated Name"

    def test_valid_isin_metadata_formats(self):
        """Test various valid ISIN formats for metadata."""
        valid_isins = [
            "IE00B4L5Y983",  # Irish ISIN
            "US0378331005",  # US ISIN
            "GB0002374006",  # UK ISIN
            "DE0005140008",  # German ISIN
        ]

        for isin in valid_isins:
            metadata = ISINMetadataCreate(
                isin=isin,
                name="Test Asset",
                type=ISINType.STOCK
            )
            assert metadata.isin == isin


class TestOtherAssetSchemas:
    """Test other asset schema validation."""

    def test_other_asset_create_valid_crypto(self):
        """Test creating valid crypto asset schema."""
        asset = OtherAssetCreate(
            asset_type=AssetType.CRYPTO,
            asset_detail=None,
            currency=Currency.EUR,
            value=Decimal("700.00")
        )

        assert asset.asset_type == AssetType.CRYPTO
        assert asset.asset_detail is None
        assert asset.currency == Currency.EUR
        assert asset.value == Decimal("700.00")

    def test_other_asset_create_valid_cash_eur(self):
        """Test creating valid cash EUR asset with account."""
        asset = OtherAssetCreate(
            asset_type=AssetType.CASH_EUR,
            asset_detail="CSOB",
            currency=Currency.EUR,
            value=Decimal("1500.00")
        )

        assert asset.asset_type == AssetType.CASH_EUR
        assert asset.asset_detail == "CSOB"
        assert asset.currency == Currency.EUR

    def test_other_asset_create_cannot_create_investments(self):
        """Test that investments asset type cannot be manually created."""
        with pytest.raises(ValidationError) as exc_info:
            OtherAssetCreate(
                asset_type=AssetType.INVESTMENTS,
                asset_detail=None,
                currency=Currency.EUR,
                value=Decimal("10000.00")
            )

        assert "investments" in str(exc_info.value).lower()

    def test_other_asset_create_cash_requires_account(self):
        """Test that cash assets require account name."""
        with pytest.raises(ValidationError) as exc_info:
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail=None,  # Missing account name
                currency=Currency.EUR,
                value=Decimal("1000.00")
            )

        assert "account name" in str(exc_info.value).lower()

    def test_other_asset_create_invalid_account_name(self):
        """Test that invalid account names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="InvalidBank",  # Not in VALID_ACCOUNT_NAMES
                currency=Currency.EUR,
                value=Decimal("1000.00")
            )

        assert "invalid account name" in str(exc_info.value).lower()

    def test_other_asset_create_non_cash_cannot_have_account(self):
        """Test that non-cash assets cannot have asset_detail."""
        with pytest.raises(ValidationError) as exc_info:
            OtherAssetCreate(
                asset_type=AssetType.CRYPTO,
                asset_detail="CSOB",  # Should be None for crypto
                currency=Currency.EUR,
                value=Decimal("700.00")
            )

        assert "must not have" in str(exc_info.value).lower()

    def test_other_asset_create_currency_mismatch_cash_eur(self):
        """Test that cash_eur requires EUR currency."""
        with pytest.raises(ValidationError) as exc_info:
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.CZK,  # Wrong currency
                value=Decimal("1000.00")
            )

        assert "currency mismatch" in str(exc_info.value).lower()

    def test_other_asset_create_currency_mismatch_cash_czk(self):
        """Test that cash_czk requires CZK currency."""
        with pytest.raises(ValidationError) as exc_info:
            OtherAssetCreate(
                asset_type=AssetType.CASH_CZK,
                asset_detail="CSOB",
                currency=Currency.EUR,  # Wrong currency
                value=Decimal("1000.00")
            )

        assert "currency mismatch" in str(exc_info.value).lower()

    def test_other_asset_create_negative_value_rejected(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError):
            OtherAssetCreate(
                asset_type=AssetType.CRYPTO,
                asset_detail=None,
                currency=Currency.EUR,
                value=Decimal("-100.00")
            )

    def test_other_asset_create_zero_value_accepted(self):
        """Test that zero value is accepted (unlike position values)."""
        asset = OtherAssetCreate(
            asset_type=AssetType.CRYPTO,
            asset_detail=None,
            currency=Currency.EUR,
            value=Decimal("0.00")
        )

        assert asset.value == Decimal("0.00")
