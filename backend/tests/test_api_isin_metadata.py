"""Tests for ISIN metadata API endpoints."""


class TestISINMetadataAPI:
    """Test ISIN metadata API endpoints."""

    def test_create_isin_metadata(self, client):
        """Test creating new ISIN metadata via API."""
        data = {
            "isin": "IE00B4L5Y983",
            "name": "iShares Core MSCI Emerging Markets ETF",
            "type": "STOCK"
        }

        response = client.post("/api/v1/isin-metadata", json=data)

        assert response.status_code == 201
        json_data = response.json()
        assert json_data["isin"] == "IE00B4L5Y983"
        assert json_data["name"] == "iShares Core MSCI Emerging Markets ETF"
        assert json_data["type"] == "STOCK"
        assert "id" in json_data
        assert "created_at" in json_data
        assert "updated_at" in json_data

    def test_create_isin_metadata_duplicate(self, client):
        """Test creating duplicate ISIN metadata returns 409."""
        data = {"isin": "IE00B4L5Y983", "name": "First ETF", "type": "STOCK"}
        response1 = client.post("/api/v1/isin-metadata", json=data)
        assert response1.status_code == 201

        # Try to create duplicate
        duplicate_data = {"isin": "IE00B4L5Y983", "name": "Duplicate ETF", "type": "BOND"}
        response2 = client.post("/api/v1/isin-metadata", json=duplicate_data)

        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_isin_metadata_invalid_isin(self, client):
        """Test creating ISIN metadata with invalid ISIN format."""
        # Too short
        data = {"isin": "SHORT", "name": "Test ETF", "type": "STOCK"}
        response = client.post("/api/v1/isin-metadata", json=data)
        assert response.status_code == 422

        # Invalid format (starts with digits instead of letters)
        data = {"isin": "1234567890AB", "name": "Test ETF", "type": "STOCK"}
        response = client.post("/api/v1/isin-metadata", json=data)
        assert response.status_code == 422

    def test_create_isin_metadata_missing_fields(self, client):
        """Test creating ISIN metadata with missing required fields."""
        # Missing name
        data = {"isin": "IE00B4L5Y983", "type": "STOCK"}
        response = client.post("/api/v1/isin-metadata", json=data)
        assert response.status_code == 422

        # Missing type
        data = {"isin": "IE00B4L5Y983", "name": "Test ETF"}
        response = client.post("/api/v1/isin-metadata", json=data)
        assert response.status_code == 422

    def test_create_isin_metadata_invalid_type(self, client):
        """Test creating ISIN metadata with invalid type."""
        data = {"isin": "IE00B4L5Y983", "name": "Test ETF", "type": "INVALID_TYPE"}
        response = client.post("/api/v1/isin-metadata", json=data)
        assert response.status_code == 422

    def test_create_isin_metadata_normalizes_isin(self, client):
        """Test that ISIN is normalized to uppercase."""
        data = {"isin": "ie00b4l5y983", "name": "Test ETF", "type": "STOCK"}
        response = client.post("/api/v1/isin-metadata", json=data)

        assert response.status_code == 201
        assert response.json()["isin"] == "IE00B4L5Y983"

    def test_upsert_isin_metadata_create(self, client):
        """Test upserting new ISIN metadata (create) via API."""
        data = {"isin": "IE00B4L5Y983", "name": "Test ETF", "type": "STOCK"}
        response = client.post("/api/v1/isin-metadata/upsert", json=data)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["isin"] == "IE00B4L5Y983"
        assert json_data["name"] == "Test ETF"
        assert json_data["type"] == "STOCK"

    def test_upsert_isin_metadata_update(self, client):
        """Test upserting existing ISIN metadata (update) via API."""
        # Create initial metadata
        data1 = {"isin": "IE00B4L5Y983", "name": "Original Name", "type": "STOCK"}
        response1 = client.post("/api/v1/isin-metadata/upsert", json=data1)
        assert response1.status_code == 200
        id1 = response1.json()["id"]

        # Upsert with new data
        data2 = {"isin": "IE00B4L5Y983", "name": "Updated Name", "type": "BOND"}
        response2 = client.post("/api/v1/isin-metadata/upsert", json=data2)

        assert response2.status_code == 200
        json_data = response2.json()
        assert json_data["id"] == id1  # Same ID
        assert json_data["name"] == "Updated Name"
        assert json_data["type"] == "BOND"

    def test_list_isin_metadata(self, client):
        """Test listing all ISIN metadata."""
        # Create multiple metadata entries
        client.post("/api/v1/isin-metadata", json={"isin": "IE00B4L5Y983", "name": "ETF 1", "type": "STOCK"})
        client.post("/api/v1/isin-metadata", json={"isin": "US0378331005", "name": "Stock 1", "type": "STOCK"})
        client.post("/api/v1/isin-metadata", json={"isin": "GB00B24CGK77", "name": "Bond 1", "type": "BOND"})

        # List all
        response = client.get("/api/v1/isin-metadata")

        assert response.status_code == 200
        json_data = response.json()
        assert "items" in json_data
        assert "total" in json_data
        assert json_data["total"] == 3
        assert len(json_data["items"]) == 3

    def test_list_isin_metadata_empty(self, client):
        """Test listing ISIN metadata when none exist."""
        response = client.get("/api/v1/isin-metadata")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["total"] == 0
        assert json_data["items"] == []

    def test_list_isin_metadata_filter_by_type(self, client):
        """Test listing ISIN metadata filtered by type."""
        # Create mixed types
        client.post("/api/v1/isin-metadata", json={"isin": "IE00B4L5Y983", "name": "ETF 1", "type": "STOCK"})
        client.post("/api/v1/isin-metadata", json={"isin": "US0378331005", "name": "Stock 1", "type": "STOCK"})
        client.post("/api/v1/isin-metadata", json={"isin": "GB00B24CGK77", "name": "Bond 1", "type": "BOND"})
        client.post("/api/v1/isin-metadata", json={"isin": "DE0005933931", "name": "Real Asset 1", "type": "REAL_ASSET"})

        # Filter by STOCK
        response = client.get("/api/v1/isin-metadata?type=STOCK")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["total"] == 2
        assert all(item["type"] == "STOCK" for item in json_data["items"])

        # Filter by BOND
        response = client.get("/api/v1/isin-metadata?type=BOND")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["total"] == 1
        assert json_data["items"][0]["type"] == "BOND"

        # Filter by REAL_ASSET
        response = client.get("/api/v1/isin-metadata?type=REAL_ASSET")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["total"] == 1
        assert json_data["items"][0]["type"] == "REAL_ASSET"

    def test_get_isin_metadata_by_isin(self, client):
        """Test getting specific ISIN metadata by ISIN."""
        # Create metadata
        client.post("/api/v1/isin-metadata", json={"isin": "IE00B4L5Y983", "name": "Test ETF", "type": "STOCK"})

        # Get by ISIN
        response = client.get("/api/v1/isin-metadata/IE00B4L5Y983")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["isin"] == "IE00B4L5Y983"
        assert json_data["name"] == "Test ETF"
        assert json_data["type"] == "STOCK"

    def test_get_isin_metadata_not_found(self, client):
        """Test getting non-existent ISIN metadata returns 404."""
        response = client.get("/api/v1/isin-metadata/NONEXISTENT1")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_isin_metadata(self, client):
        """Test updating ISIN metadata."""
        # Create metadata
        client.post("/api/v1/isin-metadata", json={"isin": "IE00B4L5Y983", "name": "Original Name", "type": "STOCK"})

        # Update both fields
        update_data = {"name": "Updated Name", "type": "BOND"}
        response = client.put("/api/v1/isin-metadata/IE00B4L5Y983", json=update_data)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["isin"] == "IE00B4L5Y983"
        assert json_data["name"] == "Updated Name"
        assert json_data["type"] == "BOND"

    def test_update_isin_metadata_partial(self, client):
        """Test updating only some fields of ISIN metadata."""
        # Create metadata
        client.post("/api/v1/isin-metadata", json={"isin": "IE00B4L5Y983", "name": "Original Name", "type": "STOCK"})

        # Update only name
        update_data = {"name": "New Name"}
        response = client.put("/api/v1/isin-metadata/IE00B4L5Y983", json=update_data)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["name"] == "New Name"
        assert json_data["type"] == "STOCK"  # Should remain unchanged

    def test_update_isin_metadata_not_found(self, client):
        """Test updating non-existent ISIN metadata returns 404."""
        update_data = {"name": "Updated Name"}
        response = client.put("/api/v1/isin-metadata/NONEXISTENT1", json=update_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_isin_metadata(self, client):
        """Test deleting ISIN metadata."""
        # Create metadata
        client.post("/api/v1/isin-metadata", json={"isin": "IE00B4L5Y983", "name": "Test ETF", "type": "STOCK"})

        # Delete
        response = client.delete("/api/v1/isin-metadata/IE00B4L5Y983")

        assert response.status_code == 204

        # Verify deleted
        get_response = client.get("/api/v1/isin-metadata/IE00B4L5Y983")
        assert get_response.status_code == 404

    def test_delete_isin_metadata_not_found(self, client):
        """Test deleting non-existent ISIN metadata returns 404."""
        response = client.delete("/api/v1/isin-metadata/NONEXISTENT1")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
