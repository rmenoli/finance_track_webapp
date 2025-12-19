"""Tests for other assets API endpoints."""

from decimal import Decimal


class TestOtherAssetsAPI:
    """Test other assets API endpoints."""

    def test_upsert_other_asset_create_crypto(self, client):
        """Test creating a new crypto asset via API."""
        data = {
            "asset_type": "crypto",
            "asset_detail": None,
            "currency": "EUR",
            "value": "700.00"
        }

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
            "value": "1500.00"
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
        data1 = {
            "asset_type": "crypto",
            "asset_detail": None,
            "currency": "EUR",
            "value": "700.00"
        }
        response1 = client.post("/api/v1/other-assets", json=data1)
        assert response1.status_code == 200
        id1 = response1.json()["id"]

        # Update with new value
        data2 = {
            "asset_type": "crypto",
            "asset_detail": None,
            "currency": "EUR",
            "value": "850.00"
        }
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
            "value": "10000.00"
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
            "value": "1000.00"
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
            "value": "1000.00"
        }

        response = client.post("/api/v1/other-assets", json=data)

        assert response.status_code == 422

    def test_upsert_other_asset_non_cash_cannot_have_account(self, client):
        """Test that non-cash assets cannot have asset_detail."""
        data = {
            "asset_type": "crypto",
            "asset_detail": "CSOB",  # Should be None for crypto
            "currency": "EUR",
            "value": "700.00"
        }

        response = client.post("/api/v1/other-assets", json=data)

        assert response.status_code == 422

    def test_list_other_assets_with_investments(self, client):
        """Test listing all assets including synthetic investments row."""
        # Create a crypto asset
        data = {
            "asset_type": "crypto",
            "asset_detail": None,
            "currency": "EUR",
            "value": "700.00"
        }
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
        data = {
            "asset_type": "crypto",
            "asset_detail": None,
            "currency": "EUR",
            "value": "700.00"
        }
        client.post("/api/v1/other-assets", json=data)

        # List without investments
        response = client.get("/api/v1/other-assets?include_investments=false")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["total"] == 1

        # Should not have investments row
        types = [asset["asset_type"] for asset in json_data["other_assets"]]
        assert "investments" not in types

    def test_get_other_asset_by_type(self, client):
        """Test getting a specific asset by type."""
        # Create crypto asset
        data = {
            "asset_type": "crypto",
            "asset_detail": None,
            "currency": "EUR",
            "value": "700.00"
        }
        client.post("/api/v1/other-assets", json=data)

        # Get by type
        response = client.get("/api/v1/other-assets/crypto")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["asset_type"] == "crypto"
        assert Decimal(json_data["value"]) == Decimal("700.00")

    def test_get_other_asset_by_type_and_account(self, client):
        """Test getting a specific cash asset by type and account."""
        # Create cash asset
        data = {
            "asset_type": "cash_eur",
            "asset_detail": "CSOB",
            "currency": "EUR",
            "value": "1500.00"
        }
        client.post("/api/v1/other-assets", json=data)

        # Get by type and account
        response = client.get("/api/v1/other-assets/cash_eur?asset_detail=CSOB")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["asset_type"] == "cash_eur"
        assert json_data["asset_detail"] == "CSOB"

    def test_get_other_asset_not_found(self, client):
        """Test getting non-existent asset returns 404."""
        response = client.get("/api/v1/other-assets/nonexistent")

        assert response.status_code == 404

    def test_delete_other_asset(self, client):
        """Test deleting an asset."""
        # Create asset
        data = {
            "asset_type": "crypto",
            "asset_detail": None,
            "currency": "EUR",
            "value": "700.00"
        }
        client.post("/api/v1/other-assets", json=data)

        # Delete
        response = client.delete("/api/v1/other-assets/crypto")

        assert response.status_code == 204

        # Verify deleted
        response = client.get("/api/v1/other-assets/crypto")
        assert response.status_code == 404

    def test_delete_other_asset_not_found(self, client):
        """Test deleting non-existent asset returns 404."""
        response = client.delete("/api/v1/other-assets/nonexistent")

        assert response.status_code == 404
