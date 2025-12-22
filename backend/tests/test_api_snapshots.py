"""Tests for asset snapshots API endpoints."""

from datetime import datetime
from decimal import Decimal

from app.constants import AssetType, Currency
from app.schemas.other_asset import OtherAssetCreate
from app.services import asset_snapshot_service, other_asset_service
from app.services.user_setting_service import update_exchange_rate_setting


class TestSnapshotsAPI:
    """Test asset snapshots API endpoints."""

    def test_get_snapshot_summary_endpoint(self, client, db_session):
        """Test GET /snapshots/summary endpoint returns correct aggregated data."""
        # Set exchange rate
        update_exchange_rate_setting(db_session, Decimal("25.00"))

        # Create various assets
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CRYPTO,
                asset_detail=None,
                currency=Currency.EUR,
                value=Decimal("500.00")
            )
        )
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
                asset_type=AssetType.CD_ACCOUNT,
                asset_detail=None,
                currency=Currency.CZK,
                value=Decimal("2500.00")
            )
        )

        # Create two snapshots at different dates
        date1 = datetime(2024, 1, 1, 10, 0, 0)
        date2 = datetime(2024, 2, 1, 10, 0, 0)
        asset_snapshot_service.create_snapshot(db_session, date1)
        asset_snapshot_service.create_snapshot(db_session, date2)

        # Test API endpoint
        response = client.get("/api/v1/snapshots/summary")

        # Verify response
        assert response.status_code == 200
        json_data = response.json()

        # Check structure
        assert "summaries" in json_data
        assert "total" in json_data
        assert json_data["total"] == 2

        summaries = json_data["summaries"]
        assert len(summaries) == 2

        # Check ordering (DESC by date)
        assert summaries[0]["snapshot_date"] > summaries[1]["snapshot_date"]

        # Check first summary (date2 - most recent)
        summary = summaries[0]
        assert "snapshot_date" in summary
        assert "total_value_eur" in summary
        assert "exchange_rate_used" in summary
        assert "by_currency" in summary
        assert "by_asset_type" in summary

        # Verify total EUR value (500 + 1000 + 100 (2500/25))
        assert Decimal(summary["total_value_eur"]) == Decimal("1600.00")

        # Verify currency breakdown
        by_currency = {c["currency"]: Decimal(c["total_value"]) for c in summary["by_currency"]}
        assert "EUR" in by_currency
        assert "CZK" in by_currency
        assert by_currency["EUR"] == Decimal("1500.00")  # crypto + cash_eur + investments(0)
        assert by_currency["CZK"] == Decimal("2500.00")  # cd_account

        # Verify asset type breakdown
        by_asset_type = {a["asset_type"]: Decimal(a["total_value_eur"]) for a in summary["by_asset_type"]}
        assert "investments" in by_asset_type
        assert "crypto" in by_asset_type
        assert "cash_eur" in by_asset_type
        assert "cd_account" in by_asset_type
        assert by_asset_type["crypto"] == Decimal("500.00")
        assert by_asset_type["cash_eur"] == Decimal("1000.00")
        assert by_asset_type["cd_account"] == Decimal("100.00")  # 2500 / 25

    def test_get_snapshot_summary_with_date_filters(self, client, db_session):
        """Test GET /snapshots/summary with date range filters."""
        # Create three snapshots
        date1 = datetime(2024, 1, 1, 10, 0, 0)
        date2 = datetime(2024, 2, 1, 10, 0, 0)
        date3 = datetime(2024, 3, 1, 10, 0, 0)

        asset_snapshot_service.create_snapshot(db_session, date1)
        asset_snapshot_service.create_snapshot(db_session, date2)
        asset_snapshot_service.create_snapshot(db_session, date3)

        # Test with start_date filter
        response = client.get(
            f"/api/v1/snapshots/summary?start_date={date2.isoformat()}"
        )
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["total"] == 2  # date2 and date3

        # Test with end_date filter
        response = client.get(
            f"/api/v1/snapshots/summary?end_date={date2.isoformat()}"
        )
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["total"] == 2  # date1 and date2

    def test_get_snapshot_summary_empty(self, client):
        """Test GET /snapshots/summary returns empty list when no snapshots exist."""
        response = client.get("/api/v1/snapshots/summary")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["summaries"] == []
        assert json_data["total"] == 0
