"""ISIN metadata service for business logic."""

import logging
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.constants import ISINType
from app.exceptions import ISINMetadataAlreadyExistsError, ISINMetadataNotFoundError
from app.logging_config import log_with_context
from app.models.isin_metadata import ISINMetadata
from app.schemas.isin_metadata import ISINMetadataCreate, ISINMetadataUpdate

logger = logging.getLogger(__name__)


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

        # AUDIT LOG
        log_with_context(
            logger,
            logging.INFO,
            "ISIN metadata created",
            operation="CREATE",
            isin=isin_normalized,
            isin_name=metadata_data.name,
            isin_type=metadata_data.type.value,
        )

        return isin_metadata
    except IntegrityError as e:
        db.rollback()

        # LOG ROLLBACK - previously silent
        log_with_context(
            logger,
            logging.WARNING,
            "ISIN metadata creation failed - IntegrityError",
            isin=isin_normalized,
            error_type=type(e).__name__,
            error_message=str(e),
        )

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

    # Track changes for audit log
    changes = {}

    # Update only provided fields
    if metadata_update.name is not None and isin_metadata.name != metadata_update.name:
        changes["isin_name"] = {"before": isin_metadata.name, "after": metadata_update.name}
        isin_metadata.name = metadata_update.name

    if metadata_update.type is not None and isin_metadata.type != metadata_update.type:
        changes["isin_type"] = {
            "before": isin_metadata.type.value,
            "after": metadata_update.type.value,
        }
        isin_metadata.type = metadata_update.type

    # updated_at will auto-update via onupdate in model
    db.commit()
    db.refresh(isin_metadata)

    # AUDIT LOG
    if changes:
        log_with_context(
            logger,
            logging.INFO,
            "ISIN metadata updated",
            operation="UPDATE",
            isin=isin_metadata.isin,
            changes=changes,
        )

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

    # Store for audit log
    deleted_data = {
        "isin": isin_metadata.isin,
        "isin_name": isin_metadata.name,
        "isin_type": isin_metadata.type.value,
    }

    db.delete(isin_metadata)
    db.commit()

    # AUDIT LOG
    log_with_context(
        logger,
        logging.INFO,
        "ISIN metadata deleted",
        operation="DELETE",
        **deleted_data,
    )


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
        # Track changes
        changes = {}
        if existing.name != metadata_data.name:
            changes["isin_name"] = {"before": existing.name, "after": metadata_data.name}
        if existing.type != metadata_data.type:
            changes["isin_type"] = {
                "before": existing.type.value,
                "after": metadata_data.type.value,
            }

        existing.name = metadata_data.name
        existing.type = metadata_data.type
        # updated_at will auto-update via onupdate in model
        db.commit()
        db.refresh(existing)

        # AUDIT LOG - UPDATE
        log_with_context(
            logger,
            logging.INFO,
            "ISIN metadata upserted (updated)",
            operation="UPSERT_UPDATE",
            isin=isin_normalized,
            changes=changes,
        )

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

        # AUDIT LOG - CREATE
        log_with_context(
            logger,
            logging.INFO,
            "ISIN metadata upserted (created)",
            operation="UPSERT_CREATE",
            isin=isin_normalized,
            isin_name=metadata_data.name,
            isin_type=metadata_data.type.value,
        )

        return isin_metadata
