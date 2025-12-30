"""Tests for other assets API endpoints."""

from datetime import date
from decimal import Decimal

from app.constants import AssetType, Currency, TransactionType
from app.schemas.other_asset import OtherAssetCreate
from app.schemas.position_value import PositionValueCreate
from app.schemas.transaction import TransactionCreate
from app.services import (
    other_asset_service,
    position_value_service,
    transaction_service,
    user_setting_service,
)


class TestOtherAssetsAPI:
    """Test other assets API endpoints."""

    def test_upsert_other_asset_create_crypto(self, client):
        """Test creating a new crypto asset via API."""
        data = {"asset_type": "crypto", "asset_detail": None, "currency": "EUR", "value": "700.00"}

        response = client.post("/api/v1/other-assets", json=data)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["asset_type"] == "crypto"
        assert json_data["asset_detail"] is None
        assert json_data["currency"] == "EUR"
        assert Decimal(json_data["value"]) == Decimal("700.00")
        assert "id" in json_data
        assert "created_at" in json_data
        assert "updated_at" in json_data

    def test_upsert_other_asset_create_cash_eur(self, client):
        """Test creating a cash EUR asset with account name."""
        data = {
            "asset_type": "cash_eur",
            "asset_detail": "CSOB",
            "currency": "EUR",
            "value": "1500.00",
        }

        response = client.post("/api/v1/other-assets", json=data)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["asset_type"] == "cash_eur"
        assert json_data["asset_detail"] == "CSOB"
        assert json_data["currency"] == "EUR"
        assert Decimal(json_data["value"]) == Decimal("1500.00")

    def test_upsert_other_asset_update(self, client):
        """Test updating an existing asset via API."""
        # Create initial asset
        data1 = {"asset_type": "crypto", "asset_detail": None, "currency": "EUR", "value": "700.00"}
        response1 = client.post("/api/v1/other-assets", json=data1)
        assert response1.status_code == 200
        id1 = response1.json()["id"]

        # Update with new value
        data2 = {"asset_type": "crypto", "asset_detail": None, "currency": "EUR", "value": "850.00"}
        response2 = client.post("/api/v1/other-assets", json=data2)

        assert response2.status_code == 200
        json_data = response2.json()
        assert json_data["id"] == id1  # Same ID
        assert Decimal(json_data["value"]) == Decimal("850.00")

    def test_upsert_other_asset_cannot_create_investments(self, client):
        """Test that investments asset type cannot be manually created."""
        data = {
            "asset_type": "investments",
            "asset_detail": None,
            "currency": "EUR",
            "value": "10000.00",
        }

        response = client.post("/api/v1/other-assets", json=data)

        assert response.status_code == 422  # Validation error
        assert "investments" in response.json()["detail"][0]["msg"]

    def test_upsert_other_asset_cash_requires_account(self, client):
        """Test that cash assets require account name."""
        data = {
            "asset_type": "cash_eur",
            "asset_detail": None,  # Missing account name
            "currency": "EUR",
            "value": "1000.00",
        }

        response = client.post("/api/v1/other-assets", json=data)

        assert response.status_code == 422
        assert "account name" in response.json()["detail"][0]["msg"].lower()

    def test_upsert_other_asset_invalid_account_name(self, client):
        """Test that invalid account names are rejected."""
        data = {
            "asset_type": "cash_eur",
            "asset_detail": "InvalidBank",  # Not in VALID_ACCOUNT_NAMES
            "currency": "EUR",
            "value": "1000.00",
        }

        response = client.post("/api/v1/other-assets", json=data)

        assert response.status_code == 422

    def test_upsert_other_asset_non_cash_cannot_have_account(self, client):
        """Test that non-cash assets cannot have asset_detail."""
        data = {
            "asset_type": "crypto",
            "asset_detail": "CSOB",  # Should be None for crypto
            "currency": "EUR",
            "value": "700.00",
        }

        response = client.post("/api/v1/other-assets", json=data)

        assert response.status_code == 422

    def test_list_other_assets_with_investments(self, client):
        """Test listing all assets including synthetic investments row."""
        # Create a crypto asset
        data = {"asset_type": "crypto", "asset_detail": None, "currency": "EUR", "value": "700.00"}
        client.post("/api/v1/other-assets", json=data)

        # List all with investments (default)
        response = client.get("/api/v1/other-assets")

        assert response.status_code == 200
        json_data = response.json()
        assert "other_assets" in json_data
        assert "total" in json_data
        assert json_data["total"] >= 1

        # First asset should be investments (synthetic)
        investments = json_data["other_assets"][0]
        assert investments["asset_type"] == "investments"
        assert investments["id"] == 0  # Marker for synthetic

    def test_list_other_assets_without_investments(self, client):
        """Test listing assets without synthetic investments row."""
        # Create a crypto asset
        data = {"asset_type": "crypto", "asset_detail": None, "currency": "EUR", "value": "700.00"}
        client.post("/api/v1/other-assets", json=data)

        # List without investments
        response = client.get("/api/v1/other-assets?include_investments=false")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["total"] == 1

        # Should not have investments row
        types = [asset["asset_type"] for asset in json_data["other_assets"]]
        assert "investments" not in types

    def test_delete_other_asset(self, client):
        """Test deleting an asset."""
        # Create asset
        data = {"asset_type": "crypto", "asset_detail": None, "currency": "EUR", "value": "700.00"}
        client.post("/api/v1/other-assets", json=data)

        # Delete
        response = client.delete("/api/v1/other-assets/crypto")

        assert response.status_code == 204

        # Verify deleted by listing all assets
        response = client.get("/api/v1/other-assets?include_investments=false")
        assert response.status_code == 200
        types = [asset["asset_type"] for asset in response.json()["other_assets"]]
        assert "crypto" not in types

    def test_delete_other_asset_not_found(self, client):
        """Test deleting non-existent asset returns 404."""
        response = client.delete("/api/v1/other-assets/nonexistent")

        assert response.status_code == 404

    def test_exchange_rate_affects_value_eur(self, client):
        """Test that changing exchange rate updates EUR conversion for CZK assets."""
        # Create a CZK asset worth 2500 CZK
        czk_asset_data = {
            "asset_type": "cd_account",
            "asset_detail": None,
            "currency": "CZK",
            "value": "2500.00",
        }
        client.post("/api/v1/other-assets", json=czk_asset_data)

        # Get with default exchange rate (25.00)
        response = client.get("/api/v1/other-assets")
        assets = response.json()["other_assets"]
        cd_account = next(a for a in assets if a["asset_type"] == "cd_account")

        # 2500 CZK / 25.00 = 100.00 EUR
        assert Decimal(cd_account["value_eur"]) == Decimal("100.00")
        assert Decimal(response.json()["exchange_rate_used"]) == Decimal("25.00")

        # Update exchange rate to 24.00
        client.post("/api/v1/settings/exchange-rate", json={"exchange_rate": 24.00})

        # Get again with new exchange rate
        response = client.get("/api/v1/other-assets")
        assets = response.json()["other_assets"]
        cd_account = next(a for a in assets if a["asset_type"] == "cd_account")

        # 2500 CZK / 24.00 = 104.17 EUR (rounded)
        assert abs(Decimal(cd_account["value_eur"]) - Decimal("104.166667")) < Decimal("0.01")
        assert Decimal(response.json()["exchange_rate_used"]) == Decimal("24.00")

        # EUR assets should not be affected by exchange rate
        eur_asset_data = {
            "asset_type": "crypto",
            "asset_detail": None,
            "currency": "EUR",
            "value": "500.00",
        }
        client.post("/api/v1/other-assets", json=eur_asset_data)

        response = client.get("/api/v1/other-assets")
        assets = response.json()["other_assets"]
        crypto = next(a for a in assets if a["asset_type"] == "crypto")

        # EUR assets should have value_eur == value
        assert Decimal(crypto["value_eur"]) == Decimal("500.00")


class TestMonthlyExpectedReturns:
    """Test monthly expected return calculations in other assets response."""

    def test_monthly_returns_with_defaults(self, client, db_session):
        """Test monthly returns calculated with default rates."""
        # Setup: Create transaction for investments value
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Test",
                units=Decimal("10.0"),
                price_per_unit=Decimal("100.0"),
                transaction_type=TransactionType.BUY,
                fee=Decimal("0.0"),
            ),
        )

        # Create position value (sets current value to €1200)
        position_value_service.upsert_position_value(
            db_session,
            PositionValueCreate(isin="IE00B4L5Y983", current_value=Decimal("1200.0")),
        )

        # Create CD account (€600)
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CD_ACCOUNT,
                asset_detail=None,
                currency=Currency.CZK,
                value=Decimal("600.0"),
            ),
        )

        # Get assets
        response = client.get("/api/v1/other-assets?include_investments=true")

        assert response.status_code == 200
        data = response.json()

        # Verify monthly returns
        # Investment: (1200 EUR * 7%) / 12 = 7.00 EUR/month
        assert Decimal(data["monthly_expected_return_investment"]) == Decimal("7.00")

        # CD: 600 CZK / 25 = 24 EUR, then (24 EUR * 4%) / 12 = 0.08 EUR/month
        assert Decimal(data["monthly_expected_return_cd"]) == Decimal("0.08")

    def test_monthly_returns_with_zero_values(self, client, db_session):
        """Test monthly returns when asset values are zero."""
        response = client.get("/api/v1/other-assets?include_investments=true")

        assert response.status_code == 200
        data = response.json()

        # Both should be 0.00 when no assets
        assert data["monthly_expected_return_investment"] == "0.00"
        assert data["monthly_expected_return_cd"] == "0.00"

    def test_monthly_returns_with_custom_rates(self, client, db_session):
        """Test monthly returns with custom expected return rates."""
        # Create CD account
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CD_ACCOUNT,
                asset_detail=None,
                currency=Currency.CZK,
                value=Decimal("1000.0"),
            ),
        )

        # Set custom CD rate to 6%
        user_setting_service.update_expected_return_cd_setting(db_session, Decimal("6.00"))

        response = client.get("/api/v1/other-assets?include_investments=true")

        assert response.status_code == 200
        data = response.json()

        # CD: 1000 CZK / 25 = 40 EUR, then (40 EUR * 6%) / 12 = 0.20 EUR/month
        assert Decimal(data["monthly_expected_return_cd"]) == Decimal("0.20")

    def test_monthly_returns_sums_multiple_cd_accounts(self, client, db_session):
        """Test that multiple CD accounts are summed correctly."""
        # Create CD account
        other_asset_service.upsert_other_asset(
            db_session,
            OtherAssetCreate(
                asset_type=AssetType.CD_ACCOUNT,
                asset_detail=None,
                currency=Currency.CZK,
                value=Decimal("400.0"),
            ),
        )

        response = client.get("/api/v1/other-assets?include_investments=true")

        assert response.status_code == 200
        data = response.json()

        # CD: 400 CZK / 25 = 16 EUR, then (16 EUR * 4%) / 12 = 0.05 EUR/month
        assert Decimal(data["monthly_expected_return_cd"]) == Decimal("0.05")

    def test_monthly_returns_excluded_when_investments_false(self, client, db_session):
        """Test that monthly returns are 0.00 when include_investments=false."""
        response = client.get("/api/v1/other-assets?include_investments=false")

        assert response.status_code == 200
        data = response.json()

        # Both should be 0.00 when investments not included
        assert data["monthly_expected_return_investment"] == "0.00"
        assert data["monthly_expected_return_cd"] == "0.00"
