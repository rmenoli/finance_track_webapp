"""Tests for transaction API endpoints."""
from datetime import date, timedelta
from io import BytesIO


class TestTransactionAPI:
    """Test transaction API endpoints."""

    def test_create_transaction_success(self, client):
        """Test creating a transaction via API."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Interactive Brokers",
                "fee": 1.50,
                "price_per_unit": 450.25,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["isin"] == "IE00B4L5Y983"
        assert data["broker"] == "Interactive Brokers"
        assert data["transaction_type"] == "BUY"

    def test_create_transaction_validation_error_future_date(self, client):
        """Test that future dates are rejected."""
        future_date = date.today() + timedelta(days=1)
        response = client.post(
            "/api/v1/transactions",
            json={
                "date": str(future_date),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )

        assert response.status_code == 422
        assert "future" in response.json()["detail"][0]["msg"].lower()

    def test_create_transaction_validation_error_invalid_isin(self, client):
        """Test that invalid ISIN format is rejected."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "INVALID",  # Too short
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )

        assert response.status_code == 422

    def test_create_transaction_validation_error_negative_units(self, client):
        """Test that negative units are rejected."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": -10.0,  # Negative
                "transaction_type": "BUY"
            }
        )

        assert response.status_code == 422

    def test_create_transaction_validation_error_negative_price(self, client):
        """Test that negative price is rejected."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": -100.00,  # Negative
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )

        assert response.status_code == 422

    def test_create_transaction_validation_error_negative_fee(self, client):
        """Test that negative fee is rejected."""
        response = client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": -1.00,  # Negative
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )

        assert response.status_code == 422

    def test_list_transactions_empty(self, client):
        """Test listing transactions when database is empty."""
        response = client.get("/api/v1/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data["transactions"] == []
        assert data["total"] == 0
        assert data["skip"] == 0
        assert data["limit"] == 100

    def test_list_transactions_with_data(self, client):
        """Test listing transactions."""
        # Create transactions
        for i in range(3):
            client.post(
                "/api/v1/transactions",
                json={
                    "date": str(date.today() - timedelta(days=i)),
                    "isin": "IE00B4L5Y983",
                    "broker": f"Broker {i}",
                    "fee": 1.00,
                    "price_per_unit": 100.00,
                    "units": 10.0,
                    "transaction_type": "BUY"
                }
            )

        response = client.get("/api/v1/transactions")

        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 3
        assert data["total"] == 3

    def test_list_transactions_filter_by_isin(self, client):
        """Test filtering transactions by ISIN."""
        # Create transactions with different ISINs
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "US0378331005",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 200.00,
                "units": 5.0,
                "transaction_type": "BUY"
            }
        )

        response = client.get("/api/v1/transactions?isin=IE00B4L5Y983")

        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 1
        assert data["transactions"][0]["isin"] == "IE00B4L5Y983"

    def test_list_transactions_filter_by_broker(self, client):
        """Test filtering transactions by broker."""
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Interactive Brokers",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Degiro",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )

        response = client.get("/api/v1/transactions?broker=Interactive%20Brokers")

        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 1
        assert data["transactions"][0]["broker"] == "Interactive Brokers"

    def test_list_transactions_filter_by_type(self, client):
        """Test filtering transactions by type."""
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )
        client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 110.00,
                "units": 5.0,
                "transaction_type": "SELL"
            }
        )

        response = client.get("/api/v1/transactions?transaction_type=BUY")

        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 1
        assert data["transactions"][0]["transaction_type"] == "BUY"

    def test_list_transactions_pagination(self, client):
        """Test transaction pagination."""
        # Create 5 transactions
        for i in range(5):
            client.post(
                "/api/v1/transactions",
                json={
                    "date": str(date.today() - timedelta(days=i)),
                    "isin": "IE00B4L5Y983",
                    "broker": "Broker",
                    "fee": 1.00,
                    "price_per_unit": 100.00,
                    "units": 10.0,
                    "transaction_type": "BUY"
                }
            )

        # Get first 2
        response = client.get("/api/v1/transactions?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 2
        assert data["total"] == 5

    def test_get_transaction_by_id(self, client):
        """Test getting a single transaction by ID."""
        # Create transaction
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )
        transaction_id = create_response.json()["id"]

        # Get transaction
        response = client.get(f"/api/v1/transactions/{transaction_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transaction_id
        assert data["isin"] == "IE00B4L5Y983"

    def test_get_transaction_not_found(self, client):
        """Test getting a non-existent transaction."""
        response = client.get("/api/v1/transactions/999")

        assert response.status_code == 404

    def test_update_transaction(self, client):
        """Test updating a transaction."""
        # Create transaction
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Old Broker",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )
        transaction_id = create_response.json()["id"]

        # Update transaction
        response = client.put(
            f"/api/v1/transactions/{transaction_id}",
            json={
                "broker": "New Broker",
                "fee": 2.00
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["broker"] == "New Broker"
        assert data["fee"] == "2.00"
        assert data["isin"] == "IE00B4L5Y983"  # Unchanged

    def test_update_transaction_not_found(self, client):
        """Test updating a non-existent transaction."""
        response = client.put(
            "/api/v1/transactions/999",
            json={"broker": "New Broker"}
        )

        assert response.status_code == 404

    def test_delete_transaction(self, client):
        """Test deleting a transaction."""
        # Create transaction
        create_response = client.post(
            "/api/v1/transactions",
            json={
                "date": str(date.today()),
                "isin": "IE00B4L5Y983",
                "broker": "Broker",
                "fee": 1.00,
                "price_per_unit": 100.00,
                "units": 10.0,
                "transaction_type": "BUY"
            }
        )
        transaction_id = create_response.json()["id"]

        # Delete transaction
        response = client.delete(f"/api/v1/transactions/{transaction_id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/v1/transactions/{transaction_id}")
        assert get_response.status_code == 404

    def test_delete_transaction_not_found(self, client):
        """Test deleting a non-existent transaction."""
        response = client.delete("/api/v1/transactions/999")

        assert response.status_code == 404

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data

    def test_degiro_import_csv_transactions_success(self, client):
        """Test successful CSV import via API."""
        csv_content = b"""Date,Time,Product,ISIN,Reference exchange,Venue,Quantity,Price,,Local value,,Value EUR,Exchange rate,AutoFX Fee,Transaction and/or third party fees EUR,Total EUR,Order ID,
11-12-2024,16:03,VANGUARD FTSE ALL-WORLD...,IE00BK5BQT80,XET,XETA,21,"143,9000",EUR,"-3021,90",EUR,"-3021,90",,"0,00","-3,00","-3024,90",,b1d87359
10-12-2024,10:30,APPLE INC,US0378331005,NDQ,XNAS,-10,"450,25",USD,"4502,50",EUR,"4000,00","1,125","0,00","-1,50","3998,50",,c2e98460"""

        response = client.post(
            "/api/v1/transactions/degiro-import-csv-transactions",
            files={"file": ("degiro.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 2
        assert data["successful"] == 2
        assert data["failed"] == 0
        assert data["success_rate"] == 100.0
        assert len(data["results"]) == 2
        assert len(data["errors"]) == 0

        # Verify first transaction (BUY)
        assert data["results"][0]["row"] == 1
        assert data["results"][0]["isin"] == "IE00BK5BQT80"
        assert data["results"][0]["transaction_type"] == "BUY"

        # Verify second transaction (SELL)
        assert data["results"][1]["row"] == 2
        assert data["results"][1]["isin"] == "US0378331005"
        assert data["results"][1]["transaction_type"] == "SELL"

    def test_degiro_import_csv_transactions_with_validation_errors(self, client):
        """Test CSV import with validation errors."""
        # Future date that will fail validation
        future_date = (date.today() + timedelta(days=365)).strftime("%d-%m-%Y")
        csv_content = f"""Date,Time,Product,ISIN,Reference exchange,Venue,Quantity,Price,,Local value,,Value EUR,Exchange rate,AutoFX Fee,Transaction and/or third party fees EUR,Total EUR,Order ID,
{future_date},16:03,FUTURE DATE,IE00BK5BQT80,XET,XETA,21,"143,9000",EUR,"-3021,90",EUR,"-3021,90",,"0,00","-3,00","-3024,90",,bad1""".encode()

        response = client.post(
            "/api/v1/transactions/degiro-import-csv-transactions",
            files={"file": ("degiro.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 1
        assert data["successful"] == 0
        assert data["failed"] == 1
        assert len(data["errors"]) == 1
        assert "future" in data["errors"][0]["errors"][0].lower()

    def test_degiro_import_csv_transactions_invalid_file_type(self, client):
        """Test CSV import rejects non-CSV files."""
        txt_content = b"not a csv file"

        response = client.post(
            "/api/v1/transactions/degiro-import-csv-transactions",
            files={"file": ("data.txt", BytesIO(txt_content), "text/plain")},
        )

        assert response.status_code == 400
        assert "must be a CSV file" in response.json()["detail"]

    def test_degiro_import_csv_transactions_invalid_utf8(self, client):
        """Test CSV import rejects non-UTF-8 files."""
        # Create invalid UTF-8 bytes
        invalid_utf8 = b"\x80\x81\x82\x83"

        response = client.post(
            "/api/v1/transactions/degiro-import-csv-transactions",
            files={"file": ("degiro.csv", BytesIO(invalid_utf8), "text/csv")},
        )

        assert response.status_code == 400
        assert "UTF-8" in response.json()["detail"]

    def test_degiro_import_csv_transactions_missing_columns(self, client):
        """Test CSV import with missing required columns."""
        csv_content = b"""Date,Time,ISIN
11-12-2024,16:03,IE00BK5BQT80"""

        response = client.post(
            "/api/v1/transactions/degiro-import-csv-transactions",
            files={"file": ("degiro.csv", BytesIO(csv_content), "text/csv")},
        )

        assert response.status_code == 400
        assert "Missing required columns" in response.json()["detail"]
