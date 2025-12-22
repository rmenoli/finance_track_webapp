"""Tests for user_setting_service."""

from decimal import Decimal

import pytest

from app.services import user_setting_service


class TestUserSettingService:
    """Test user setting service functions."""

    def test_get_exchange_rate_not_set(self, db_session):
        """Test getting exchange rate when not set returns None."""
        rate = user_setting_service.get_exchange_rate_setting(db_session)
        assert rate is None

    def test_update_exchange_rate_create(self, db_session):
        """Test creating exchange rate setting."""
        rate = Decimal("24.50")
        setting = user_setting_service.update_exchange_rate_setting(db_session, rate)

        assert setting.setting_key == user_setting_service.EXCHANGE_RATE_KEY
        assert setting.setting_value == "24.50"
        assert setting.id is not None

    def test_update_exchange_rate_update(self, db_session):
        """Test updating existing exchange rate setting."""
        # Create initial
        user_setting_service.update_exchange_rate_setting(db_session, Decimal("24.50"))

        # Update
        setting = user_setting_service.update_exchange_rate_setting(db_session, Decimal("26.00"))

        assert setting.setting_value == "26.00"

        # Verify only one record exists
        retrieved = user_setting_service.get_exchange_rate_setting(db_session)
        assert retrieved is not None
        assert Decimal(retrieved.setting_value) == Decimal("26.00")

    def test_get_exchange_rate_after_create(self, db_session):
        """Test getting exchange rate after creating."""
        user_setting_service.update_exchange_rate_setting(db_session, Decimal("25.75"))

        setting = user_setting_service.get_exchange_rate_setting(db_session)
        assert setting is not None
        assert Decimal(setting.setting_value) == Decimal("25.75")
