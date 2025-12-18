"""Tests for position value service."""

from decimal import Decimal

import pytest

from app.exceptions import PositionValueNotFoundError
from app.schemas.position_value import PositionValueCreate
from app.services import position_value_service


class TestPositionValueService:
    """Test position value service CRUD operations."""

    def test_upsert_position_value_create(self, db_session):
        """Test creating a new position value."""
        pv_data = PositionValueCreate(
            isin="IE00B4L5Y983",
            current_value=Decimal("5000.50")
        )

        position_value = position_value_service.upsert_position_value(db_session, pv_data)

        assert position_value.id is not None
        assert position_value.isin == "IE00B4L5Y983"
        assert position_value.current_value == Decimal("5000.50")
        assert position_value.created_at is not None
        assert position_value.updated_at is not None

    def test_upsert_position_value_update(self, db_session):
        """Test updating an existing position value."""
        # Create initial value
        pv_data = PositionValueCreate(
            isin="IE00B4L5Y983",
            current_value=Decimal("5000.50")
        )
        initial = position_value_service.upsert_position_value(db_session, pv_data)
        initial_id = initial.id
        initial_created_at = initial.created_at

        # Update with new value
        pv_update = PositionValueCreate(
            isin="IE00B4L5Y983",
            current_value=Decimal("6000.75")
        )
        updated = position_value_service.upsert_position_value(db_session, pv_update)

        # Verify it's the same record with updated value
        assert updated.id == initial_id
        assert updated.isin == "IE00B4L5Y983"
        assert updated.current_value == Decimal("6000.75")
        assert updated.created_at == initial_created_at  # Should not change
        assert updated.updated_at >= initial.updated_at  # Should update

    def test_upsert_normalizes_isin(self, db_session):
        """Test that ISIN is normalized to uppercase."""
        pv_data = PositionValueCreate(
            isin="ie00b4l5y983",  # lowercase
            current_value=Decimal("1000.00")
        )

        position_value = position_value_service.upsert_position_value(db_session, pv_data)

        assert position_value.isin == "IE00B4L5Y983"  # Should be uppercase

    def test_get_position_value(self, db_session):
        """Test getting a position value by ISIN."""
        # Create position value
        pv_data = PositionValueCreate(
            isin="IE00B4L5Y983",
            current_value=Decimal("5000.50")
        )
        created = position_value_service.upsert_position_value(db_session, pv_data)

        # Get by ISIN
        retrieved = position_value_service.get_position_value(db_session, "IE00B4L5Y983")

        assert retrieved.id == created.id
        assert retrieved.isin == "IE00B4L5Y983"
        assert retrieved.current_value == Decimal("5000.50")

    def test_get_position_value_not_found(self, db_session):
        """Test getting non-existent position value raises error."""
        with pytest.raises(PositionValueNotFoundError):
            position_value_service.get_position_value(db_session, "NONEXISTENT1")

    def test_get_all_position_values(self, db_session):
        """Test getting all position values."""
        # Create multiple position values
        pv1 = PositionValueCreate(isin="IE00B4L5Y983", current_value=Decimal("1000.00"))
        pv2 = PositionValueCreate(isin="US0378331005", current_value=Decimal("2000.00"))
        pv3 = PositionValueCreate(isin="GB00B24CGK77", current_value=Decimal("3000.00"))

        position_value_service.upsert_position_value(db_session, pv1)
        position_value_service.upsert_position_value(db_session, pv2)
        position_value_service.upsert_position_value(db_session, pv3)

        # Get all
        all_values = position_value_service.get_all_position_values(db_session)

        assert len(all_values) == 3
        isins = [pv.isin for pv in all_values]
        assert "IE00B4L5Y983" in isins
        assert "US0378331005" in isins
        assert "GB00B24CGK77" in isins

    def test_get_all_position_values_empty(self, db_session):
        """Test getting all position values when none exist."""
        all_values = position_value_service.get_all_position_values(db_session)

        assert all_values == []

    def test_delete_position_value(self, db_session):
        """Test deleting a position value."""
        # Create position value
        pv_data = PositionValueCreate(
            isin="IE00B4L5Y983",
            current_value=Decimal("5000.50")
        )
        position_value_service.upsert_position_value(db_session, pv_data)

        # Delete
        position_value_service.delete_position_value(db_session, "IE00B4L5Y983")

        # Verify deleted
        with pytest.raises(PositionValueNotFoundError):
            position_value_service.get_position_value(db_session, "IE00B4L5Y983")

    def test_delete_position_value_not_found(self, db_session):
        """Test deleting non-existent position value raises error."""
        with pytest.raises(PositionValueNotFoundError):
            position_value_service.delete_position_value(db_session, "NONEXISTENT1")
