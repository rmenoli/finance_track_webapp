"""Tests for expected return settings API endpoints and service layer."""

from decimal import Decimal


class TestExpectedReturnInvestmentAPI:
    """Test expected return investment API endpoints."""

    def test_get_not_set_returns_default(self, client, db_session):
        """Test GET when not set returns default 7.00."""
        response = client.get("/api/v1/settings/expected-return-investment")

        assert response.status_code == 200
        data = response.json()
        assert data["expected_return"] == "7.00"
        assert "updated_at" in data

    def test_update_valid(self, client, db_session):
        """Test POST with valid percentage."""
        response = client.post(
            "/api/v1/settings/expected-return-investment", json={"expected_return": 8.50}
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["expected_return"]) == Decimal("8.50")
        assert "updated_at" in data

    def test_update_invalid_negative(self, client, db_session):
        """Test POST with negative value."""
        response = client.post(
            "/api/v1/settings/expected-return-investment", json={"expected_return": -1.0}
        )

        assert response.status_code == 422  # Validation error

    def test_update_invalid_over_100(self, client, db_session):
        """Test POST with value > 100."""
        response = client.post(
            "/api/v1/settings/expected-return-investment", json={"expected_return": 101.0}
        )

        assert response.status_code == 422  # Validation error

    def test_update_boundary_zero(self, client, db_session):
        """Test POST with zero value (valid)."""
        response = client.post(
            "/api/v1/settings/expected-return-investment", json={"expected_return": 0.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["expected_return"] == "0.00"

    def test_update_boundary_100(self, client, db_session):
        """Test POST with 100% value (valid)."""
        response = client.post(
            "/api/v1/settings/expected-return-investment", json={"expected_return": 100.0}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["expected_return"] == "100.00"

    def test_get_after_update(self, client, db_session):
        """Test GET returns updated value."""
        # Update
        client.post("/api/v1/settings/expected-return-investment", json={"expected_return": 9.25})

        # Get
        response = client.get("/api/v1/settings/expected-return-investment")

        assert response.status_code == 200
        data = response.json()
        assert data["expected_return"] == "9.25"

    def test_update_upsert_semantics(self, client, db_session):
        """Test multiple updates use UPSERT (only one record)."""
        # First update
        client.post("/api/v1/settings/expected-return-investment", json={"expected_return": 5.0})

        # Second update
        client.post("/api/v1/settings/expected-return-investment", json={"expected_return": 10.0})

        # Should have latest value
        response = client.get("/api/v1/settings/expected-return-investment")
        data = response.json()
        assert data["expected_return"] == "10.00"


class TestExpectedReturnCDAPI:
    """Test expected return CD API endpoints."""

    def test_get_not_set_returns_default(self, client, db_session):
        """Test GET when not set returns default 4.00."""
        response = client.get("/api/v1/settings/expected-return-cd")

        assert response.status_code == 200
        data = response.json()
        assert data["expected_return"] == "4.00"
        assert "updated_at" in data

    def test_update_valid(self, client, db_session):
        """Test POST with valid percentage."""
        response = client.post(
            "/api/v1/settings/expected-return-cd", json={"expected_return": 3.75}
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["expected_return"]) == Decimal("3.75")
        assert "updated_at" in data

    def test_update_invalid_negative(self, client, db_session):
        """Test POST with negative value."""
        response = client.post(
            "/api/v1/settings/expected-return-cd", json={"expected_return": -1.0}
        )

        assert response.status_code == 422  # Validation error

    def test_update_invalid_over_100(self, client, db_session):
        """Test POST with value > 100."""
        response = client.post(
            "/api/v1/settings/expected-return-cd", json={"expected_return": 150.0}
        )

        assert response.status_code == 422  # Validation error

    def test_get_after_update(self, client, db_session):
        """Test GET returns updated value."""
        # Update
        client.post("/api/v1/settings/expected-return-cd", json={"expected_return": 5.50})

        # Get
        response = client.get("/api/v1/settings/expected-return-cd")

        assert response.status_code == 200
        data = response.json()
        assert data["expected_return"] == "5.50"


class TestExpectedReturnServiceLayer:
    """Test expected return service layer functions."""

    def test_get_investment_not_set(self, db_session):
        """Test getting investment return when not set returns None."""
        from app.services import user_setting_service

        rate = user_setting_service.get_expected_return_investment_setting(db_session)
        assert rate is None

    def test_update_investment_create(self, db_session):
        """Test creating investment return setting."""
        from app.services import user_setting_service

        rate = Decimal("7.50")
        setting = user_setting_service.update_expected_return_investment_setting(db_session, rate)

        assert setting.setting_key == user_setting_service.EXPECTED_RETURN_INVESTMENT_KEY
        assert setting.setting_value == "7.50"
        assert setting.id is not None

    def test_update_investment_update(self, db_session):
        """Test updating existing investment return setting."""
        from app.services import user_setting_service

        # Create initial
        user_setting_service.update_expected_return_investment_setting(db_session, Decimal("7.00"))

        # Update
        setting = user_setting_service.update_expected_return_investment_setting(
            db_session, Decimal("8.00")
        )

        assert setting.setting_value == "8.00"

        # Verify only one record exists
        retrieved = user_setting_service.get_expected_return_investment_setting(db_session)
        assert retrieved is not None
        assert Decimal(retrieved.setting_value) == Decimal("8.00")

    def test_get_cd_not_set(self, db_session):
        """Test getting CD return when not set returns None."""
        from app.services import user_setting_service

        rate = user_setting_service.get_expected_return_cd_setting(db_session)
        assert rate is None

    def test_update_cd_create(self, db_session):
        """Test creating CD return setting."""
        from app.services import user_setting_service

        rate = Decimal("4.25")
        setting = user_setting_service.update_expected_return_cd_setting(db_session, rate)

        assert setting.setting_key == user_setting_service.EXPECTED_RETURN_CD_KEY
        assert setting.setting_value == "4.25"
        assert setting.id is not None

    def test_update_cd_update(self, db_session):
        """Test updating existing CD return setting."""
        from app.services import user_setting_service

        # Create initial
        user_setting_service.update_expected_return_cd_setting(db_session, Decimal("4.00"))

        # Update
        setting = user_setting_service.update_expected_return_cd_setting(
            db_session, Decimal("5.00")
        )

        assert setting.setting_value == "5.00"

        # Verify only one record exists
        retrieved = user_setting_service.get_expected_return_cd_setting(db_session)
        assert retrieved is not None
        assert Decimal(retrieved.setting_value) == Decimal("5.00")
