"""ISIN metadata service for business logic."""

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.constants import ISINType
from app.exceptions import ISINMetadataAlreadyExistsError, ISINMetadataNotFoundError
from app.models.isin_metadata import ISINMetadata
from app.schemas.isin_metadata import ISINMetadataCreate, ISINMetadataUpdate


def create_isin_metadata(
    db: Session,
    metadata_data: ISINMetadataCreate
) -> ISINMetadata:
    """
    Create new ISIN metadata.

    Args:
        db: Database session
        metadata_data: ISIN metadata data

    Returns:
        Created ISIN metadata

    Raises:
        ISINMetadataAlreadyExistsError: If ISIN already exists
    """
    # Normalize ISIN to uppercase for consistency
    isin_normalized = metadata_data.isin.upper()

    # Check if ISIN metadata already exists
    existing = db.query(ISINMetadata).filter(
        ISINMetadata.isin == isin_normalized
    ).first()

    if existing:
        raise ISINMetadataAlreadyExistsError(isin_normalized)

    # Create new record
    isin_metadata = ISINMetadata(
        isin=isin_normalized,
        name=metadata_data.name,
        type=metadata_data.type
    )

    try:
        db.add(isin_metadata)
        db.commit()
        db.refresh(isin_metadata)
        return isin_metadata
    except IntegrityError:
        db.rollback()
        raise ISINMetadataAlreadyExistsError(isin_normalized)


def get_isin_metadata(db: Session, isin: str) -> ISINMetadata:
    """
    Get ISIN metadata by ISIN.

    Args:
        db: Database session
        isin: ISIN code

    Returns:
        ISIN metadata

    Raises:
        ISINMetadataNotFoundError: If ISIN metadata not found
    """
    isin_normalized = isin.upper()

    isin_metadata = db.query(ISINMetadata).filter(
        ISINMetadata.isin == isin_normalized
    ).first()

    if not isin_metadata:
        raise ISINMetadataNotFoundError(isin_normalized)

    return isin_metadata


def get_all_isin_metadata(
    db: Session,
    asset_type: Optional[ISINType] = None
) -> list[ISINMetadata]:
    """
    Get all ISIN metadata with optional filtering by type.

    Args:
        db: Database session
        asset_type: Optional filter by asset type

    Returns:
        List of ISIN metadata ordered by ISIN
    """
    query = db.query(ISINMetadata)

    # Apply type filter if provided
    if asset_type:
        query = query.filter(ISINMetadata.type == asset_type)

    return query.order_by(ISINMetadata.isin.asc()).all()


def update_isin_metadata(
    db: Session,
    isin: str,
    metadata_update: ISINMetadataUpdate
) -> ISINMetadata:
    """
    Update ISIN metadata.

    Args:
        db: Database session
        isin: ISIN code
        metadata_update: Updated ISIN metadata data

    Returns:
        Updated ISIN metadata

    Raises:
        ISINMetadataNotFoundError: If ISIN metadata not found
    """
    isin_metadata = get_isin_metadata(db, isin)

    # Update only provided fields
    if metadata_update.name is not None:
        isin_metadata.name = metadata_update.name

    if metadata_update.type is not None:
        isin_metadata.type = metadata_update.type

    # updated_at will auto-update via onupdate in model
    db.commit()
    db.refresh(isin_metadata)
    return isin_metadata


def delete_isin_metadata(db: Session, isin: str) -> None:
    """
    Delete ISIN metadata by ISIN.

    Args:
        db: Database session
        isin: ISIN code

    Raises:
        ISINMetadataNotFoundError: If ISIN metadata not found
    """
    isin_metadata = get_isin_metadata(db, isin)
    db.delete(isin_metadata)
    db.commit()


def upsert_isin_metadata(
    db: Session,
    metadata_data: ISINMetadataCreate
) -> ISINMetadata:
    """
    Create or update ISIN metadata (UPSERT operation).

    If ISIN exists, updates the name and type.
    If ISIN doesn't exist, creates new record.

    Args:
        db: Database session
        metadata_data: ISIN metadata data

    Returns:
        Created or updated ISIN metadata
    """
    # Normalize ISIN to uppercase for consistency
    isin_normalized = metadata_data.isin.upper()

    # Check if ISIN metadata exists
    existing = db.query(ISINMetadata).filter(
        ISINMetadata.isin == isin_normalized
    ).first()

    if existing:
        # Update existing record
        existing.name = metadata_data.name
        existing.type = metadata_data.type
        # updated_at will auto-update via onupdate in model
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new record
        isin_metadata = ISINMetadata(
            isin=isin_normalized,
            name=metadata_data.name,
            type=metadata_data.type
        )
        db.add(isin_metadata)
        db.commit()
        db.refresh(isin_metadata)
        return isin_metadata
