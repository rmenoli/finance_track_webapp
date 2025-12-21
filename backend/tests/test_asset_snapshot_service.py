"""Tests for asset snapshot service."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.constants import AssetType, Currency
from app.exceptions import SnapshotNotFoundError
from app.models.transaction import Transaction
from app.schemas.other_asset import OtherAssetCreate
from app.schemas.position_value import PositionValueCreate
from app.services import asset_snapshot_service, other_asset_service, position_value_service
from app.services.user_setting_service import update_exchange_rate_setting


class TestAssetSnapshotService:
    """Test asset snapshot service operations."""

    # Creation tests

    def test_create_snapshot_with_investments_and_assets(self, db_session):
        """Test creating snapshot with both investments and other assets."""
        # Create transaction with position value (investments)
        transaction = Transaction(
            isin="IE00B4L5Y983",
            broker="DEGIRO",
            date=datetime(2024, 1, 1),
            transaction_type="BUY",
            units=Decimal("10.00"),
            price_per_unit=Decimal("100.00"),
            fee=Decimal("5.00")
        )
        db_session.add(transaction)
        db_session.commit()

        # Add position value
        position_value_service.upsert_position_value(
            db_session,
            PositionValueCreate(isin="IE00B4L5Y983", current_value=Decimal("1200.00"))
        )

        # Create other assets
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CRYPTO,
                asset_detail=None,
                currency=Currency.EUR,
                value=Decimal("500.00")
            )
        )

        # Create snapshot
        snapshots, metadata = asset_snapshot_service.create_snapshot(db_session)

        # Verify
        assert len(snapshots) == 2  # investments + crypto
        assert metadata.total_assets_captured == 2
        assert metadata.total_value_eur == Decimal("1700.00")  # 1200 + 500

        # Check investments row
        investments = next(s for s in snapshots if s.asset_type == "investments")
        assert investments.value == Decimal("1200.00")
        assert investments.currency == "EUR"
        assert investments.asset_detail is None

        # Check crypto row
        crypto = next(s for s in snapshots if s.asset_type == "crypto")
        assert crypto.value == Decimal("500.00")
        assert crypto.currency == "EUR"

    def test_create_snapshot_empty_portfolio(self, db_session):
        """Test creating snapshot with empty portfolio (investments=0)."""
        snapshots, metadata = asset_snapshot_service.create_snapshot(db_session)

        # Should have investments row with value 0
        assert len(snapshots) == 1
        assert snapshots[0].asset_type == "investments"
        assert snapshots[0].value == Decimal("0")
        assert metadata.total_value_eur == Decimal("0")

    def test_create_snapshot_only_investments(self, db_session):
        """Test creating snapshot with only ETF holdings (no other assets)."""
        # Create transaction with position value
        transaction = Transaction(
            isin="IE00B4L5Y983",
            broker="DEGIRO",
            date=datetime(2024, 1, 1),
            transaction_type="BUY",
            units=Decimal("10.00"),
            price_per_unit=Decimal("100.00"),
            fee=Decimal("5.00")
        )
        db_session.add(transaction)
        db_session.commit()

        position_value_service.upsert_position_value(
            db_session,
            PositionValueCreate(isin="IE00B4L5Y983", current_value=Decimal("1200.00"))
        )

        # Create snapshot
        snapshots, metadata = asset_snapshot_service.create_snapshot(db_session)

        # Should have only investments row
        assert len(snapshots) == 1
        assert snapshots[0].asset_type == "investments"
        assert snapshots[0].value == Decimal("1200.00")
        assert metadata.total_value_eur == Decimal("1200.00")

    def test_create_snapshot_only_other_assets(self, db_session):
        """Test creating snapshot with only other assets (no transactions)."""
        # Create other assets
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CRYPTO,
                asset_detail=None,
                currency=Currency.EUR,
                value=Decimal("500.00")
            )
        )

        # Create snapshot
        snapshots, metadata = asset_snapshot_service.create_snapshot(db_session)

        # Should have investments (0) + crypto
        assert len(snapshots) == 2
        investments = next(s for s in snapshots if s.asset_type == "investments")
        assert investments.value == Decimal("0")

        crypto = next(s for s in snapshots if s.asset_type == "crypto")
        assert crypto.value == Decimal("500.00")

    def test_create_snapshot_stores_each_cash_account_separately(self, db_session):
        """Test that multiple cash accounts are stored as separate rows (no aggregation)."""
        # Create multiple EUR cash accounts
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("1000.00")
            )
        )
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="RAIF",
                currency=Currency.EUR,
                value=Decimal("500.00")
            )
        )

        # Create snapshot
        snapshots, metadata = asset_snapshot_service.create_snapshot(db_session)

        # Should have investments + 2 separate cash_eur rows
        assert len(snapshots) == 3
        cash_eur_snapshots = [s for s in snapshots if s.asset_type == "cash_eur"]
        assert len(cash_eur_snapshots) == 2

        # Verify each account is separate
        csob = next(s for s in cash_eur_snapshots if s.asset_detail == "CSOB")
        assert csob.value == Decimal("1000.00")

        raif = next(s for s in cash_eur_snapshots if s.asset_detail == "RAIF")
        assert raif.value == Decimal("500.00")

        # Total should be sum of all
        assert metadata.total_value_eur == Decimal("1500.00")

    def test_create_snapshot_with_custom_datetime(self, db_session):
        """Test creating snapshot with custom datetime."""
        custom_date = datetime(2024, 6, 15, 10, 30, 0)

        snapshots, metadata = asset_snapshot_service.create_snapshot(
            db_session, custom_date
        )

        assert len(snapshots) >= 1
        assert snapshots[0].snapshot_date == custom_date
        assert metadata.snapshot_date == custom_date

    def test_create_snapshot_calculates_value_eur_correctly(self, db_session):
        """Test that value_eur is calculated correctly for CZK assets."""
        # Set exchange rate
        update_exchange_rate_setting(db_session, Decimal("24.00"))

        # Create CZK asset
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CD_ACCOUNT,
                asset_detail=None,
                currency=Currency.CZK,
                value=Decimal("2400.00")
            )
        )

        # Create snapshot
        snapshots, metadata = asset_snapshot_service.create_snapshot(db_session)

        # Find CD account snapshot
        cd_account = next(s for s in snapshots if s.asset_type == "cd_account")
        assert cd_account.value == Decimal("2400.00")
        assert cd_account.currency == "CZK"
        assert cd_account.exchange_rate == Decimal("24.00")
        assert cd_account.value_eur == Decimal("100.00")  # 2400 / 24

    def test_create_snapshot_includes_asset_detail(self, db_session):
        """Test that asset_detail is stored correctly for cash accounts."""
        # Create cash account with detail
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="Wise",
                currency=Currency.EUR,
                value=Decimal("300.00")
            )
        )

        # Create crypto (no detail)
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CRYPTO,
                asset_detail=None,
                currency=Currency.EUR,
                value=Decimal("500.00")
            )
        )

        # Create snapshot
        snapshots, _ = asset_snapshot_service.create_snapshot(db_session)

        # Verify asset_detail
        cash = next(s for s in snapshots if s.asset_type == "cash_eur")
        assert cash.asset_detail == "Wise"

        crypto = next(s for s in snapshots if s.asset_type == "crypto")
        assert crypto.asset_detail is None

        investments = next(s for s in snapshots if s.asset_type == "investments")
        assert investments.asset_detail is None

    # Query tests

    def test_get_snapshots_no_filters(self, db_session):
        """Test getting all snapshots without filters."""
        # Create two snapshots on different dates
        date1 = datetime(2024, 1, 1, 10, 0, 0)
        date2 = datetime(2024, 1, 2, 10, 0, 0)

        asset_snapshot_service.create_snapshot(db_session, date1)
        asset_snapshot_service.create_snapshot(db_session, date2)

        # Get all snapshots
        snapshots = asset_snapshot_service.get_snapshots(db_session)

        # Should have 2 snapshots * assets per snapshot
        assert len(snapshots) >= 2

    def test_get_snapshots_with_date_range(self, db_session):
        """Test querying snapshots with date range filters."""
        # Create snapshots on different dates
        date1 = datetime(2024, 1, 1, 10, 0, 0)
        date2 = datetime(2024, 1, 15, 10, 0, 0)
        date3 = datetime(2024, 2, 1, 10, 0, 0)

        asset_snapshot_service.create_snapshot(db_session, date1)
        asset_snapshot_service.create_snapshot(db_session, date2)
        asset_snapshot_service.create_snapshot(db_session, date3)

        # Query with date range (Jan 10 - Jan 20)
        snapshots = asset_snapshot_service.get_snapshots(
            db_session,
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 20)
        )

        # Should only have Jan 15 snapshots
        assert all(s.snapshot_date == date2 for s in snapshots)

    def test_get_snapshots_with_asset_type_filter(self, db_session):
        """Test filtering snapshots by asset type."""
        # Create assets
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CRYPTO,
                asset_detail=None,
                currency=Currency.EUR,
                value=Decimal("500.00")
            )
        )

        asset_snapshot_service.create_snapshot(db_session)

        # Query only crypto snapshots
        snapshots = asset_snapshot_service.get_snapshots(
            db_session, asset_type="crypto"
        )

        assert len(snapshots) == 1
        assert snapshots[0].asset_type == "crypto"

    def test_get_snapshots_by_date(self, db_session):
        """Test getting snapshots for a specific date."""
        snapshot_date = datetime(2024, 6, 15, 10, 0, 0)

        # Create snapshot
        created_snapshots, _ = asset_snapshot_service.create_snapshot(
            db_session, snapshot_date
        )

        # Get by date
        snapshots = asset_snapshot_service.get_snapshots_by_date(
            db_session, snapshot_date
        )

        assert len(snapshots) == len(created_snapshots)
        assert all(s.snapshot_date == snapshot_date for s in snapshots)

    def test_get_snapshots_by_date_not_found(self, db_session):
        """Test getting snapshots for non-existent date raises error."""
        with pytest.raises(SnapshotNotFoundError):
            asset_snapshot_service.get_snapshots_by_date(
                db_session, datetime(2024, 12, 31)
            )

    def test_get_snapshots_ordering(self, db_session):
        """Test that snapshots are ordered by date DESC, asset_type ASC."""
        # Create snapshots on different dates
        date1 = datetime(2024, 1, 1, 10, 0, 0)
        date2 = datetime(2024, 1, 2, 10, 0, 0)

        # Create assets to ensure multiple asset types
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CRYPTO,
                asset_detail=None,
                currency=Currency.EUR,
                value=Decimal("500.00")
            )
        )

        asset_snapshot_service.create_snapshot(db_session, date1)
        asset_snapshot_service.create_snapshot(db_session, date2)

        # Get all snapshots
        snapshots = asset_snapshot_service.get_snapshots(db_session)

        # Verify ordering: date DESC
        assert snapshots[0].snapshot_date >= snapshots[-1].snapshot_date

    # Deletion tests

    def test_delete_snapshots_by_date(self, db_session):
        """Test deleting snapshots by date."""
        snapshot_date = datetime(2024, 6, 15, 10, 0, 0)

        # Create snapshot
        created_snapshots, _ = asset_snapshot_service.create_snapshot(
            db_session, snapshot_date
        )
        num_created = len(created_snapshots)

        # Delete
        deleted_count = asset_snapshot_service.delete_snapshots_by_date(
            db_session, snapshot_date
        )

        assert deleted_count == num_created

        # Verify deletion
        with pytest.raises(SnapshotNotFoundError):
            asset_snapshot_service.get_snapshots_by_date(db_session, snapshot_date)

    def test_delete_snapshots_by_date_not_found(self, db_session):
        """Test deleting non-existent snapshots raises error."""
        with pytest.raises(SnapshotNotFoundError):
            asset_snapshot_service.delete_snapshots_by_date(
                db_session, datetime(2024, 12, 31)
            )

    def test_delete_snapshots_only_deletes_specified_date(self, db_session):
        """Test that deletion only affects the specified date."""
        date1 = datetime(2024, 1, 1, 10, 0, 0)
        date2 = datetime(2024, 1, 2, 10, 0, 0)

        # Create two snapshots
        asset_snapshot_service.create_snapshot(db_session, date1)
        asset_snapshot_service.create_snapshot(db_session, date2)

        # Delete date1
        asset_snapshot_service.delete_snapshots_by_date(db_session, date1)

        # Verify date1 is gone
        with pytest.raises(SnapshotNotFoundError):
            asset_snapshot_service.get_snapshots_by_date(db_session, date1)

        # Verify date2 still exists
        snapshots = asset_snapshot_service.get_snapshots_by_date(db_session, date2)
        assert len(snapshots) >= 1

    # Edge cases

    def test_multiple_snapshots_same_date_allowed(self, db_session):
        """Test that multiple snapshots can be created on the same date."""
        snapshot_date = datetime(2024, 6, 15, 10, 0, 0)

        # Create two snapshots with same date
        asset_snapshot_service.create_snapshot(db_session, snapshot_date)
        asset_snapshot_service.create_snapshot(db_session, snapshot_date)

        # Should have snapshots from both creations
        snapshots = asset_snapshot_service.get_snapshots_by_date(
            db_session, snapshot_date
        )

        # Each creation adds at least 1 asset (investments), so should have at least 2
        assert len(snapshots) >= 2

    def test_snapshot_preserves_exchange_rate(self, db_session):
        """Test that snapshots preserve the exchange rate at creation time."""
        # Set exchange rate to 24.00
        update_exchange_rate_setting(db_session, Decimal("24.00"))

        # Create CZK asset
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CD_ACCOUNT,
                asset_detail=None,
                currency=Currency.CZK,
                value=Decimal("2400.00")
            )
        )

        # Create snapshot
        snapshots, _ = asset_snapshot_service.create_snapshot(db_session)

        # Change exchange rate
        update_exchange_rate_setting(db_session, Decimal("30.00"))

        # Verify snapshot still uses original rate
        cd_snapshot = next(s for s in snapshots if s.asset_type == "cd_account")
        assert cd_snapshot.exchange_rate == Decimal("24.00")
        assert cd_snapshot.value_eur == Decimal("100.00")  # 2400 / 24, not 2400 / 30
