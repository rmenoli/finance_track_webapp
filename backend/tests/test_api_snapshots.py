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
        assert "absolute_change_from_oldest" in summary
        assert "percentage_change_from_oldest" in summary

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
        assert Decimal(json_data["avg_monthly_increment"]) == Decimal("0.00")

    def test_snapshot_summary_percentage_change_multiple_snapshots(self, client, db_session):
        """Test percentage change calculation from oldest snapshot with multiple snapshots."""
        # Set exchange rate
        update_exchange_rate_setting(db_session, Decimal("25.00"))

        # Create assets with known values
        # First snapshot: 100 EUR total
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("100.00")
            )
        )

        date1 = datetime(2024, 1, 1, 10, 0, 0)
        asset_snapshot_service.create_snapshot(db_session, date1)

        # Second snapshot: 150 EUR total (50% increase)
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("150.00")
            )
        )

        date2 = datetime(2024, 1, 2, 10, 0, 0)
        asset_snapshot_service.create_snapshot(db_session, date2)

        # Third snapshot: 200 EUR total (100% increase from first)
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("200.00")
            )
        )

        date3 = datetime(2024, 1, 3, 10, 0, 0)
        asset_snapshot_service.create_snapshot(db_session, date3)

        # Test API endpoint
        response = client.get("/api/v1/snapshots/summary")

        assert response.status_code == 200
        summaries = response.json()["summaries"]
        assert len(summaries) == 3

        # Verify DESC order (newest first)
        assert summaries[0]["snapshot_date"].startswith("2024-01-03")
        assert summaries[1]["snapshot_date"].startswith("2024-01-02")
        assert summaries[2]["snapshot_date"].startswith("2024-01-01")

        # Verify absolute change calculations
        # Newest: 200-100 = 100
        assert Decimal(summaries[0]["absolute_change_from_oldest"]) == Decimal("100.00")
        # Middle: 150-100 = 50
        assert Decimal(summaries[1]["absolute_change_from_oldest"]) == Decimal("50.00")
        # Oldest: 100-100 = 0
        assert Decimal(summaries[2]["absolute_change_from_oldest"]) == Decimal("0.00")

        # Verify percentage calculations
        # Newest: (200-100)/100*100 = 100%
        assert Decimal(summaries[0]["percentage_change_from_oldest"]) == Decimal("100.00")
        # Middle: (150-100)/100*100 = 50%
        assert Decimal(summaries[1]["percentage_change_from_oldest"]) == Decimal("50.00")
        # Oldest: (100-100)/100*100 = 0%
        assert Decimal(summaries[2]["percentage_change_from_oldest"]) == Decimal("0.00")

    def test_snapshot_summary_percentage_change_single_snapshot(self, client, db_session):
        """Test percentage change is 0% for a single snapshot."""
        # Set exchange rate
        update_exchange_rate_setting(db_session, Decimal("25.00"))

        # Create asset
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("100.00")
            )
        )

        date1 = datetime(2024, 1, 1, 10, 0, 0)
        asset_snapshot_service.create_snapshot(db_session, date1)

        # Test API endpoint
        response = client.get("/api/v1/snapshots/summary")

        assert response.status_code == 200
        summaries = response.json()["summaries"]
        assert len(summaries) == 1

        # Single snapshot should have 0 absolute change and 0% change (baseline equals itself)
        assert Decimal(summaries[0]["absolute_change_from_oldest"]) == Decimal("0.00")
        assert Decimal(summaries[0]["percentage_change_from_oldest"]) == Decimal("0.00")

    def test_snapshot_summary_percentage_change_with_date_filter(self, client, db_session):
        """Test percentage change baseline changes with date filters."""
        # Set exchange rate
        update_exchange_rate_setting(db_session, Decimal("25.00"))

        # Create 5 snapshots with values: 100, 150, 200, 250, 300
        values = [Decimal("100.00"), Decimal("150.00"), Decimal("200.00"), Decimal("250.00"), Decimal("300.00")]
        dates = [
            datetime(2024, 1, 1, 10, 0, 0),
            datetime(2024, 1, 2, 10, 0, 0),
            datetime(2024, 1, 3, 10, 0, 0),
            datetime(2024, 1, 4, 10, 0, 0),
            datetime(2024, 1, 5, 10, 0, 0),
        ]

        for i, (value, date) in enumerate(zip(values, dates)):
            other_asset_service.upsert_other_asset(
                db_session,
                OtherAssetCreate(
                    asset_type=AssetType.CASH_EUR,
                    asset_detail="CSOB",
                    currency=Currency.EUR,
                    value=value
                )
            )
            asset_snapshot_service.create_snapshot(db_session, date)

        # Filter to get only last 3 snapshots (dates 3, 4, 5 with values 200, 250, 300)
        # Baseline should be 200 (oldest in filtered set), not 100 (global oldest)
        response = client.get(
            f"/api/v1/snapshots/summary?start_date={dates[2].isoformat()}"
        )

        assert response.status_code == 200
        summaries = response.json()["summaries"]
        assert len(summaries) == 3

        # Verify baseline is 200 (oldest in filtered set)
        # Verify absolute changes
        # Newest (300): 300-200 = 100
        assert Decimal(summaries[0]["absolute_change_from_oldest"]) == Decimal("100.00")
        # Middle (250): 250-200 = 50
        assert Decimal(summaries[1]["absolute_change_from_oldest"]) == Decimal("50.00")
        # Oldest in filtered set (200): 0
        assert Decimal(summaries[2]["absolute_change_from_oldest"]) == Decimal("0.00")

        # Verify percentage changes
        # Newest (300): (300-200)/200*100 = 50%
        assert Decimal(summaries[0]["percentage_change_from_oldest"]) == Decimal("50.00")
        # Middle (250): (250-200)/200*100 = 25%
        assert Decimal(summaries[1]["percentage_change_from_oldest"]) == Decimal("25.00")
        # Oldest in filtered set (200): 0%
        assert Decimal(summaries[2]["percentage_change_from_oldest"]) == Decimal("0.00")

    def test_snapshot_summary_percentage_change_negative_change(self, client, db_session):
        """Test percentage change correctly handles negative changes (value decrease)."""
        # Set exchange rate
        update_exchange_rate_setting(db_session, Decimal("25.00"))

        # Create snapshots with decreasing values
        # First snapshot: 200 EUR
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("200.00")
            )
        )

        date1 = datetime(2024, 1, 1, 10, 0, 0)
        asset_snapshot_service.create_snapshot(db_session, date1)

        # Second snapshot: 150 EUR (25% decrease from 200)
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("150.00")
            )
        )

        date2 = datetime(2024, 1, 2, 10, 0, 0)
        asset_snapshot_service.create_snapshot(db_session, date2)

        # Test API endpoint
        response = client.get("/api/v1/snapshots/summary")

        assert response.status_code == 200
        summaries = response.json()["summaries"]
        assert len(summaries) == 2

        # Verify absolute changes
        # Newest: 150-200 = -50
        assert Decimal(summaries[0]["absolute_change_from_oldest"]) == Decimal("-50.00")
        # Oldest: 0
        assert Decimal(summaries[1]["absolute_change_from_oldest"]) == Decimal("0.00")

        # Verify percentage changes
        # Newest: (150-200)/200*100 = -25%
        assert Decimal(summaries[0]["percentage_change_from_oldest"]) == Decimal("-25.00")
        # Oldest: 0%
        assert Decimal(summaries[1]["percentage_change_from_oldest"]) == Decimal("0.00")
    def test_snapshot_summary_avg_monthly_increment_multiple_snapshots(self, client, db_session):
        """Test avg_monthly_increment calculation with multiple snapshots."""
        # Set exchange rate
        update_exchange_rate_setting(db_session, Decimal("25.00"))

        # Create assets with known values
        # Day 0: €1000
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("1000.00")
            )
        )

        date1 = datetime(2024, 1, 1, 10, 0, 0)
        asset_snapshot_service.create_snapshot(db_session, date1)

        # Day 60: €1600 (600 increase over 60 days)
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("1600.00")
            )
        )

        date2 = datetime(2024, 3, 1, 10, 0, 0)  # 60 days later
        asset_snapshot_service.create_snapshot(db_session, date2)

        # Test API endpoint
        response = client.get("/api/v1/snapshots/summary")

        assert response.status_code == 200
        json_data = response.json()

        # Verify avg_monthly_increment is at response level
        assert "avg_monthly_increment" in json_data
        assert "summaries" in json_data
        assert "total" in json_data

        # Verify calculation: (1600-1000) / 60 * 30 = 300
        assert Decimal(json_data["avg_monthly_increment"]) == Decimal("300.00")

        # Verify it's NOT inside summaries
        for summary in json_data["summaries"]:
            assert "avg_monthly_increment" not in summary

    def test_snapshot_summary_avg_monthly_increment_single_snapshot(self, client, db_session):
        """Test avg_monthly_increment returns 0 for single snapshot."""
        # Set exchange rate
        update_exchange_rate_setting(db_session, Decimal("25.00"))

        # Create asset
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("1000.00")
            )
        )

        date1 = datetime(2024, 1, 1, 10, 0, 0)
        asset_snapshot_service.create_snapshot(db_session, date1)

        # Test API endpoint
        response = client.get("/api/v1/snapshots/summary")

        assert response.status_code == 200
        json_data = response.json()

        # Single snapshot should have 0 avg_monthly_increment
        assert Decimal(json_data["avg_monthly_increment"]) == Decimal("0.00")
        assert json_data["total"] == 1

    def test_snapshot_summary_avg_monthly_increment_empty(self, client):
        """Test avg_monthly_increment with no snapshots."""
        response = client.get("/api/v1/snapshots/summary")

        assert response.status_code == 200
        json_data = response.json()

        # Empty summaries should have 0 avg_monthly_increment
        assert json_data["summaries"] == []
        assert json_data["total"] == 0
        assert Decimal(json_data["avg_monthly_increment"]) == Decimal("0.00")

    def test_snapshot_summary_avg_monthly_increment_same_day(self, client, db_session):
        """Test avg_monthly_increment returns 0 when snapshots on same day."""
        # Set exchange rate
        update_exchange_rate_setting(db_session, Decimal("25.00"))

        # Create first snapshot
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("1000.00")
            )
        )

        date1 = datetime(2024, 1, 1, 10, 0, 0)
        asset_snapshot_service.create_snapshot(db_session, date1)

        # Create second snapshot on same day (different time)
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("1500.00")
            )
        )

        date2 = datetime(2024, 1, 1, 15, 0, 0)  # Same day, different hour
        asset_snapshot_service.create_snapshot(db_session, date2)

        # Test API endpoint
        response = client.get("/api/v1/snapshots/summary")

        assert response.status_code == 200
        json_data = response.json()

        # Same day snapshots should have 0 avg_monthly_increment (avoid division by zero)
        assert Decimal(json_data["avg_monthly_increment"]) == Decimal("0.00")
        assert json_data["total"] == 2

    def test_snapshot_summary_avg_monthly_increment_negative_growth(self, client, db_session):
        """Test avg_monthly_increment correctly handles negative growth."""
        # Set exchange rate
        update_exchange_rate_setting(db_session, Decimal("25.00"))

        # Day 0: €2000
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("2000.00")
            )
        )

        date1 = datetime(2024, 1, 1, 10, 0, 0)
        asset_snapshot_service.create_snapshot(db_session, date1)

        # Day 30: €1500 (€-500 decrease)
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CASH_EUR,
                asset_detail="CSOB",
                currency=Currency.EUR,
                value=Decimal("1500.00")
            )
        )

        date2 = datetime(2024, 1, 31, 10, 0, 0)  # 30 days later
        asset_snapshot_service.create_snapshot(db_session, date2)

        # Test API endpoint
        response = client.get("/api/v1/snapshots/summary")

        assert response.status_code == 200
        json_data = response.json()

        # Verify calculation: (1500-2000) / 30 * 30 = -500
        assert Decimal(json_data["avg_monthly_increment"]) == Decimal("-500.00")
        assert json_data["total"] == 2
