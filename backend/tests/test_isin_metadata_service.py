"""Tests for ISIN metadata service."""

import pytest

from app.constants import ISINType
from app.exceptions import ISINMetadataAlreadyExistsError, ISINMetadataNotFoundError
from app.schemas.isin_metadata import ISINMetadataCreate, ISINMetadataUpdate
from app.services import isin_metadata_service


class TestISINMetadataService:
    """Test ISIN metadata service CRUD operations."""

    def test_create_isin_metadata(self, db_session):
        """Test creating new ISIN metadata."""
        metadata_data = ISINMetadataCreate(
            isin="IE00B4L5Y983",
            name="iShares Core MSCI Emerging Markets ETF",
            type=ISINType.STOCK
        )

        metadata = isin_metadata_service.create_isin_metadata(db_session, metadata_data)

        assert metadata.id is not None
        assert metadata.isin == "IE00B4L5Y983"
        assert metadata.name == "iShares Core MSCI Emerging Markets ETF"
        assert metadata.type == ISINType.STOCK
        assert metadata.created_at is not None
        assert metadata.updated_at is not None

    def test_create_isin_metadata_duplicate(self, db_session):
        """Test creating duplicate ISIN metadata raises error."""
        metadata_data = ISINMetadataCreate(
            isin="IE00B4L5Y983",
            name="First ETF",
            type=ISINType.STOCK
        )

        # Create first metadata
        isin_metadata_service.create_isin_metadata(db_session, metadata_data)

        # Try to create duplicate
        duplicate_data = ISINMetadataCreate(
            isin="IE00B4L5Y983",
            name="Duplicate ETF",
            type=ISINType.BOND
        )

        with pytest.raises(ISINMetadataAlreadyExistsError):
            isin_metadata_service.create_isin_metadata(db_session, duplicate_data)

    def test_create_normalizes_isin(self, db_session):
        """Test that ISIN is normalized to uppercase."""
        metadata_data = ISINMetadataCreate(
            isin="ie00b4l5y983",  # lowercase
            name="Test ETF",
            type=ISINType.STOCK
        )

        metadata = isin_metadata_service.create_isin_metadata(db_session, metadata_data)

        assert metadata.isin == "IE00B4L5Y983"  # Should be uppercase

    def test_get_isin_metadata(self, db_session):
        """Test getting ISIN metadata by ISIN."""
        # Create metadata
        metadata_data = ISINMetadataCreate(
            isin="IE00B4L5Y983",
            name="Test ETF",
            type=ISINType.STOCK
        )
        created = isin_metadata_service.create_isin_metadata(db_session, metadata_data)

        # Get by ISIN
        retrieved = isin_metadata_service.get_isin_metadata(db_session, "IE00B4L5Y983")

        assert retrieved.id == created.id
        assert retrieved.isin == "IE00B4L5Y983"
        assert retrieved.name == "Test ETF"
        assert retrieved.type == ISINType.STOCK

    def test_get_isin_metadata_not_found(self, db_session):
        """Test getting non-existent ISIN metadata raises error."""
        with pytest.raises(ISINMetadataNotFoundError):
            isin_metadata_service.get_isin_metadata(db_session, "NONEXISTENT1")

    def test_get_all_isin_metadata_empty(self, db_session):
        """Test getting all ISIN metadata when database is empty."""
        all_metadata = isin_metadata_service.get_all_isin_metadata(db_session)

        assert all_metadata == []

    def test_get_all_isin_metadata(self, db_session):
        """Test getting all ISIN metadata."""
        # Create multiple metadata entries
        metadata1 = ISINMetadataCreate(isin="IE00B4L5Y983", name="ETF 1", type=ISINType.STOCK)
        metadata2 = ISINMetadataCreate(isin="US0378331005", name="Stock 1", type=ISINType.STOCK)
        metadata3 = ISINMetadataCreate(isin="GB00B24CGK77", name="Bond 1", type=ISINType.BOND)

        isin_metadata_service.create_isin_metadata(db_session, metadata1)
        isin_metadata_service.create_isin_metadata(db_session, metadata2)
        isin_metadata_service.create_isin_metadata(db_session, metadata3)

        # Get all
        all_metadata = isin_metadata_service.get_all_isin_metadata(db_session)

        assert len(all_metadata) == 3
        # Should be ordered by ISIN ascending
        assert all_metadata[0].isin == "GB00B24CGK77"
        assert all_metadata[1].isin == "IE00B4L5Y983"
        assert all_metadata[2].isin == "US0378331005"

    def test_get_all_isin_metadata_filter_by_type(self, db_session):
        """Test getting ISIN metadata filtered by type."""
        # Create mixed types
        metadata1 = ISINMetadataCreate(isin="IE00B4L5Y983", name="ETF 1", type=ISINType.STOCK)
        metadata2 = ISINMetadataCreate(isin="US0378331005", name="Stock 1", type=ISINType.STOCK)
        metadata3 = ISINMetadataCreate(isin="GB00B24CGK77", name="Bond 1", type=ISINType.BOND)
        metadata4 = ISINMetadataCreate(isin="DE0005933931", name="Real Asset 1", type=ISINType.REAL_ASSET)

        isin_metadata_service.create_isin_metadata(db_session, metadata1)
        isin_metadata_service.create_isin_metadata(db_session, metadata2)
        isin_metadata_service.create_isin_metadata(db_session, metadata3)
        isin_metadata_service.create_isin_metadata(db_session, metadata4)

        # Filter by STOCK
        stocks = isin_metadata_service.get_all_isin_metadata(db_session, asset_type=ISINType.STOCK)
        assert len(stocks) == 2
        assert all(m.type == ISINType.STOCK for m in stocks)

        # Filter by BOND
        bonds = isin_metadata_service.get_all_isin_metadata(db_session, asset_type=ISINType.BOND)
        assert len(bonds) == 1
        assert bonds[0].type == ISINType.BOND

        # Filter by REAL_ASSET
        real_assets = isin_metadata_service.get_all_isin_metadata(db_session, asset_type=ISINType.REAL_ASSET)
        assert len(real_assets) == 1
        assert real_assets[0].type == ISINType.REAL_ASSET

    def test_update_isin_metadata(self, db_session):
        """Test updating ISIN metadata."""
        # Create metadata
        metadata_data = ISINMetadataCreate(
            isin="IE00B4L5Y983",
            name="Original Name",
            type=ISINType.STOCK
        )
        created = isin_metadata_service.create_isin_metadata(db_session, metadata_data)
        created_id = created.id
        created_at = created.created_at

        # Update both fields
        update_data = ISINMetadataUpdate(
            name="Updated Name",
            type=ISINType.BOND
        )
        updated = isin_metadata_service.update_isin_metadata(db_session, "IE00B4L5Y983", update_data)

        assert updated.id == created_id
        assert updated.isin == "IE00B4L5Y983"
        assert updated.name == "Updated Name"
        assert updated.type == ISINType.BOND
        assert updated.created_at == created_at  # Should not change
        assert updated.updated_at >= created.updated_at  # Should update

    def test_update_isin_metadata_partial(self, db_session):
        """Test updating only some fields of ISIN metadata."""
        # Create metadata
        metadata_data = ISINMetadataCreate(
            isin="IE00B4L5Y983",
            name="Original Name",
            type=ISINType.STOCK
        )
        created = isin_metadata_service.create_isin_metadata(db_session, metadata_data)

        # Update only name
        update_data = ISINMetadataUpdate(name="New Name")
        updated = isin_metadata_service.update_isin_metadata(db_session, "IE00B4L5Y983", update_data)

        assert updated.name == "New Name"
        assert updated.type == ISINType.STOCK  # Should remain unchanged

        # Update only type
        update_data2 = ISINMetadataUpdate(type=ISINType.BOND)
        updated2 = isin_metadata_service.update_isin_metadata(db_session, "IE00B4L5Y983", update_data2)

        assert updated2.name == "New Name"  # Should remain unchanged
        assert updated2.type == ISINType.BOND

    def test_update_isin_metadata_not_found(self, db_session):
        """Test updating non-existent ISIN metadata raises error."""
        update_data = ISINMetadataUpdate(name="Updated Name")

        with pytest.raises(ISINMetadataNotFoundError):
            isin_metadata_service.update_isin_metadata(db_session, "NONEXISTENT1", update_data)

    def test_delete_isin_metadata(self, db_session):
        """Test deleting ISIN metadata."""
        # Create metadata
        metadata_data = ISINMetadataCreate(
            isin="IE00B4L5Y983",
            name="Test ETF",
            type=ISINType.STOCK
        )
        isin_metadata_service.create_isin_metadata(db_session, metadata_data)

        # Verify it exists
        retrieved = isin_metadata_service.get_isin_metadata(db_session, "IE00B4L5Y983")
        assert retrieved is not None

        # Delete it
        isin_metadata_service.delete_isin_metadata(db_session, "IE00B4L5Y983")

        # Verify it's gone
        with pytest.raises(ISINMetadataNotFoundError):
            isin_metadata_service.get_isin_metadata(db_session, "IE00B4L5Y983")

    def test_delete_isin_metadata_not_found(self, db_session):
        """Test deleting non-existent ISIN metadata raises error."""
        with pytest.raises(ISINMetadataNotFoundError):
            isin_metadata_service.delete_isin_metadata(db_session, "NONEXISTENT1")

    def test_upsert_isin_metadata_create(self, db_session):
        """Test upserting new ISIN metadata (create)."""
        metadata_data = ISINMetadataCreate(
            isin="IE00B4L5Y983",
            name="Test ETF",
            type=ISINType.STOCK
        )

        metadata = isin_metadata_service.upsert_isin_metadata(db_session, metadata_data)

        assert metadata.id is not None
        assert metadata.isin == "IE00B4L5Y983"
        assert metadata.name == "Test ETF"
        assert metadata.type == ISINType.STOCK

    def test_upsert_isin_metadata_update(self, db_session):
        """Test upserting existing ISIN metadata (update)."""
        # Create initial metadata
        metadata_data = ISINMetadataCreate(
            isin="IE00B4L5Y983",
            name="Original Name",
            type=ISINType.STOCK
        )
        initial = isin_metadata_service.upsert_isin_metadata(db_session, metadata_data)
        initial_id = initial.id
        initial_created_at = initial.created_at

        # Upsert with new data
        update_data = ISINMetadataCreate(
            isin="IE00B4L5Y983",
            name="Updated Name",
            type=ISINType.BOND
        )
        updated = isin_metadata_service.upsert_isin_metadata(db_session, update_data)

        # Verify it's the same record with updated values
        assert updated.id == initial_id
        assert updated.isin == "IE00B4L5Y983"
        assert updated.name == "Updated Name"
        assert updated.type == ISINType.BOND
        assert updated.created_at == initial_created_at  # Should not change
        assert updated.updated_at >= initial.updated_at  # Should update
