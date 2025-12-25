"""Tests for position values API endpoints."""

from decimal import Decimal


class TestPositionValuesAPI:
    """Test position values API endpoints."""

    def test_upsert_position_value_create(self, client):
        """Test creating a new position value via API."""
        data = {
            "isin": "IE00B4L5Y983",
            "current_value": "5000.50"
        }

        response = client.post("/api/v1/position-values", json=data)

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["isin"] == "IE00B4L5Y983"
        assert Decimal(json_data["current_value"]) == Decimal("5000.50")
        assert "id" in json_data
        assert "created_at" in json_data
        assert "updated_at" in json_data

    def test_upsert_position_value_update(self, client):
        """Test updating an existing position value via API."""
        # Create initial value
        data1 = {"isin": "IE00B4L5Y983", "current_value": "5000.50"}
        response1 = client.post("/api/v1/position-values", json=data1)
        assert response1.status_code == 200
        id1 = response1.json()["id"]

        # Update with new value
        data2 = {"isin": "IE00B4L5Y983", "current_value": "6000.75"}
        response2 = client.post("/api/v1/position-values", json=data2)

        assert response2.status_code == 200
        json_data = response2.json()
        assert json_data["id"] == id1  # Same ID
        assert Decimal(json_data["current_value"]) == Decimal("6000.75")

    def test_upsert_position_value_invalid_data(self, client):
        """Test creating position value with invalid data."""
        # Negative value
        data = {"isin": "IE00B4L5Y983", "current_value": "-100.00"}
        response = client.post("/api/v1/position-values", json=data)
        assert response.status_code == 422

        # Missing required field
        data = {"isin": "IE00B4L5Y983"}
        response = client.post("/api/v1/position-values", json=data)
        assert response.status_code == 422

    def test_list_position_values(self, client):
        """Test listing all position values."""
        # Create multiple values
        client.post("/api/v1/position-values", json={"isin": "IE00B4L5Y983", "current_value": "1000.00"})
        client.post("/api/v1/position-values", json={"isin": "US0378331005", "current_value": "2000.00"})

        # List all
        response = client.get("/api/v1/position-values")

        assert response.status_code == 200
        json_data = response.json()
        assert "position_values" in json_data
        assert "total" in json_data
        assert json_data["total"] == 2
        assert len(json_data["position_values"]) == 2

    def test_list_position_values_empty(self, client):
        """Test listing position values when none exist."""
        response = client.get("/api/v1/position-values")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["total"] == 0
        assert json_data["position_values"] == []

    def test_delete_position_value_by_id_success(self, client):
        """Test deleting position value by ID via API."""
        # Create position value
        create_response = client.post(
            "/api/v1/position-values",
            json={
                "isin": "IE00B4L5Y983",
                "current_value": 5000.00,
            },
        )
        position_value_id = create_response.json()["id"]

        # Delete by ID
        response = client.delete(f"/api/v1/position-values/{position_value_id}")

        assert response.status_code == 204

        # Verify deletion - list should be empty
        list_response = client.get("/api/v1/position-values")
        assert list_response.json()["total"] == 0

    def test_delete_position_value_by_id_not_found(self, client):
        """Test deleting non-existent position value by ID returns 404."""
        response = client.delete("/api/v1/position-values/99999")

        assert response.status_code == 404
        assert "ID 99999" in response.json()["detail"]
