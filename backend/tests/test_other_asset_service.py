"""Tests for other asset service."""

from decimal import Decimal

import pytest

from app.constants import AssetType, Currency
from app.exceptions import OtherAssetNotFoundError
from app.schemas.other_asset import OtherAssetCreate
from app.services import other_asset_service


class TestOtherAssetService:
    """Test other asset service CRUD operations."""

    def test_upsert_other_asset_create_crypto(self, db_session):
        """Test creating a new crypto asset."""
        asset_data = OtherAssetCreate(
            asset_type=AssetType.CRYPTO,
            asset_detail=None,
            currency=Currency.EUR,
            value=Decimal("700.00")
        )

        asset = other_asset_service.upsert_other_asset(db_session, asset_data)

        assert asset.id is not None
        assert asset.asset_type == AssetType.CRYPTO.value
        assert asset.asset_detail is None
        assert asset.currency == Currency.EUR.value
        assert asset.value == Decimal("700.00")
        assert asset.created_at is not None
        assert asset.updated_at is not None

    def test_upsert_other_asset_create_cash_eur(self, db_session):
        """Test creating a new cash EUR asset with account name."""
        asset_data = OtherAssetCreate(
            asset_type=AssetType.CASH_EUR,
            asset_detail="CSOB",
            currency=Currency.EUR,
            value=Decimal("1500.00")
        )

        asset = other_asset_service.upsert_other_asset(db_session, asset_data)

        assert asset.id is not None
        assert asset.asset_type == AssetType.CASH_EUR.value
        assert asset.asset_detail == "CSOB"
        assert asset.currency == Currency.EUR.value
        assert asset.value == Decimal("1500.00")

    def test_upsert_other_asset_create_cash_czk(self, db_session):
        """Test creating a new cash CZK asset with account name."""
        asset_data = OtherAssetCreate(
            asset_type=AssetType.CASH_CZK,
            asset_detail="Revolut",
            currency=Currency.CZK,
            value=Decimal("25000.00")
        )

        asset = other_asset_service.upsert_other_asset(db_session, asset_data)

        assert asset.id is not None
        assert asset.asset_type == AssetType.CASH_CZK.value
        assert asset.asset_detail == "Revolut"
        assert asset.currency == Currency.CZK.value
        assert asset.value == Decimal("25000.00")

    def test_upsert_other_asset_update(self, db_session):
        """Test updating an existing asset (same asset_type and asset_detail)."""
        # Create initial asset
        asset_data = OtherAssetCreate(
            asset_type=AssetType.CRYPTO,
            asset_detail=None,
            currency=Currency.EUR,
            value=Decimal("700.00")
        )
        initial = other_asset_service.upsert_other_asset(db_session, asset_data)
        initial_id = initial.id
        initial_created_at = initial.created_at

        # Update with new value
        asset_update = OtherAssetCreate(
            asset_type=AssetType.CRYPTO,
            asset_detail=None,
            currency=Currency.EUR,
            value=Decimal("850.00")
        )
        updated = other_asset_service.upsert_other_asset(db_session, asset_update)

        # Verify it's the same record with updated value
        assert updated.id == initial_id
        assert updated.asset_type == AssetType.CRYPTO.value
        assert updated.value == Decimal("850.00")
        assert updated.created_at == initial_created_at
        assert updated.updated_at >= initial.updated_at

    def test_upsert_other_asset_update_cash_account(self, db_session):
        """Test updating an existing cash account."""
        # Create initial cash EUR account
        asset_data = OtherAssetCreate(
            asset_type=AssetType.CASH_EUR,
            asset_detail="CSOB",
            currency=Currency.EUR,
            value=Decimal("1000.00")
        )
        initial = other_asset_service.upsert_other_asset(db_session, asset_data)

        # Update same account
        asset_update = OtherAssetCreate(
            asset_type=AssetType.CASH_EUR,
            asset_detail="CSOB",
            currency=Currency.EUR,
            value=Decimal("1500.00")
        )
        updated = other_asset_service.upsert_other_asset(db_session, asset_update)

        assert updated.id == initial.id
        assert updated.value == Decimal("1500.00")

    def test_upsert_other_asset_multiple_cash_accounts(self, db_session):
        """Test creating multiple cash accounts of same type are independent."""
        # Create CSOB account
        csob_data = OtherAssetCreate(
            asset_type=AssetType.CASH_EUR,
            asset_detail="CSOB",
            currency=Currency.EUR,
            value=Decimal("1000.00")
        )
        csob = other_asset_service.upsert_other_asset(db_session, csob_data)

        # Create Revolut account
        revolut_data = OtherAssetCreate(
            asset_type=AssetType.CASH_EUR,
            asset_detail="Revolut",
            currency=Currency.EUR,
            value=Decimal("650.00")
        )
        revolut = other_asset_service.upsert_other_asset(db_session, revolut_data)

        # Verify they are different records
        assert csob.id != revolut.id
        assert csob.asset_detail == "CSOB"
        assert revolut.asset_detail == "Revolut"

    def test_get_other_asset(self, db_session):
        """Test getting an asset by type and detail."""
        # Create asset
        asset_data = OtherAssetCreate(
            asset_type=AssetType.CRYPTO,
            asset_detail=None,
            currency=Currency.EUR,
            value=Decimal("700.00")
        )
        created = other_asset_service.upsert_other_asset(db_session, asset_data)

        # Get by type and detail
        retrieved = other_asset_service.get_other_asset(
            db_session,
            AssetType.CRYPTO.value,
            None
        )

        assert retrieved.id == created.id
        assert retrieved.asset_type == AssetType.CRYPTO.value
        assert retrieved.value == Decimal("700.00")

    def test_get_other_asset_with_account(self, db_session):
        """Test getting a cash asset by type and account name."""
        # Create cash asset
        asset_data = OtherAssetCreate(
            asset_type=AssetType.CASH_EUR,
            asset_detail="CSOB",
            currency=Currency.EUR,
            value=Decimal("1000.00")
        )
        created = other_asset_service.upsert_other_asset(db_session, asset_data)

        # Get by type and account
        retrieved = other_asset_service.get_other_asset(
            db_session,
            AssetType.CASH_EUR.value,
            "CSOB"
        )

        assert retrieved.id == created.id
        assert retrieved.asset_type == AssetType.CASH_EUR.value
        assert retrieved.asset_detail == "CSOB"

    def test_get_other_asset_not_found(self, db_session):
        """Test getting non-existent asset raises error."""
        with pytest.raises(OtherAssetNotFoundError):
            other_asset_service.get_other_asset(db_session, "nonexistent", None)

    def test_get_all_other_assets(self, db_session):
        """Test getting all assets (without synthetic investments)."""
        # Create multiple assets
        crypto_data = OtherAssetCreate(
            asset_type=AssetType.CRYPTO,
            asset_detail=None,
            currency=Currency.EUR,
            value=Decimal("700.00")
        )
        cash_data = OtherAssetCreate(
            asset_type=AssetType.CASH_EUR,
            asset_detail="CSOB",
            currency=Currency.EUR,
            value=Decimal("1000.00")
        )

        other_asset_service.upsert_other_asset(db_session, crypto_data)
        other_asset_service.upsert_other_asset(db_session, cash_data)

        # Get all (no investments)
        all_assets = other_asset_service.get_all_other_assets(db_session)

        assert len(all_assets) == 2
        types = [asset.asset_type for asset in all_assets]
        assert AssetType.CRYPTO.value in types
        assert AssetType.CASH_EUR.value in types
        assert AssetType.INVESTMENTS.value not in types

    def test_get_all_other_assets_with_investments(self, db_session):
        """Test getting all assets with synthetic investments row."""
        # Create a crypto asset
        crypto_data = OtherAssetCreate(
            asset_type=AssetType.CRYPTO,
            asset_detail=None,
            currency=Currency.EUR,
            value=Decimal("700.00")
        )
        other_asset_service.upsert_other_asset(db_session, crypto_data)

        # Get all with investments (now returns tuple)
        all_assets, exchange_rate = other_asset_service.get_all_other_assets_with_investments(db_session)

        # Should have investments row + 1 crypto = 2 total
        assert len(all_assets) >= 1

        # Exchange rate should be returned (default 25.00)
        assert exchange_rate == Decimal("25.00")

        # First item should be investments (synthetic)
        investments = all_assets[0]
        assert investments.asset_type == AssetType.INVESTMENTS.value
        assert investments.asset_detail is None
        assert investments.currency == Currency.EUR.value
        assert investments.id == 0  # Marker for synthetic

        # Check that exchange_rate_ is attached
        assert hasattr(investments, 'exchange_rate_')
        assert investments.exchange_rate_ == Decimal("25.00")

    def test_get_all_other_assets_empty(self, db_session):
        """Test getting all assets when none exist."""
        all_assets = other_asset_service.get_all_other_assets(db_session)

        assert all_assets == []

    def test_delete_other_asset(self, db_session):
        """Test deleting an asset."""
        # Create asset
        asset_data = OtherAssetCreate(
            asset_type=AssetType.CRYPTO,
            asset_detail=None,
            currency=Currency.EUR,
            value=Decimal("700.00")
        )
        other_asset_service.upsert_other_asset(db_session, asset_data)

        # Delete
        other_asset_service.delete_other_asset(
            db_session,
            AssetType.CRYPTO.value,
            None
        )

        # Verify deleted
        with pytest.raises(OtherAssetNotFoundError):
            other_asset_service.get_other_asset(db_session, AssetType.CRYPTO.value, None)

    def test_delete_other_asset_not_found(self, db_session):
        """Test deleting non-existent asset raises error."""
        with pytest.raises(OtherAssetNotFoundError):
            other_asset_service.delete_other_asset(db_session, "nonexistent", None)
