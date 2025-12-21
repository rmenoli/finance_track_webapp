"""Position value service for business logic."""

import logging

from sqlalchemy.orm import Session

from app.exceptions import PositionValueNotFoundError
from app.logging_config import log_with_context
from app.models.position_value import PositionValue
from app.schemas.position_value import PositionValueCreate
from app.services import cost_basis_service

logger = logging.getLogger(__name__)


def upsert_position_value(
    db: Session,
    position_value_data: PositionValueCreate
) -> PositionValue:
    """
    Create or update a position value (UPSERT operation).

    If ISIN exists, updates the current_value and updated_at.
    If ISIN doesn't exist, creates new record.

    Args:
        db: Database session
        position_value_data: Position value data

    Returns:
        Created or updated position value
    """
    # Normalize ISIN to uppercase for consistency
    isin_normalized = position_value_data.isin.upper()

    # Check if position value exists for this ISIN
    existing = db.query(PositionValue).filter(
        PositionValue.isin == isin_normalized
    ).first()

    if existing:
        # Update existing record
        old_value = str(existing.current_value)
        existing.current_value = position_value_data.current_value
        # updated_at will auto-update via onupdate in model
        db.commit()
        db.refresh(existing)

        # AUDIT LOG - UPDATE
        log_with_context(
            logger,
            logging.INFO,
            "Position value updated",
            operation="UPDATE",
            isin=isin_normalized,
            old_value=old_value,
            new_value=str(position_value_data.current_value),
        )

        return existing
    else:
        # Create new record
        position_value = PositionValue(
            isin=isin_normalized,
            current_value=position_value_data.current_value
        )
        db.add(position_value)
        db.commit()
        db.refresh(position_value)

        # AUDIT LOG - CREATE
        log_with_context(
            logger,
            logging.INFO,
            "Position value created",
            operation="CREATE",
            isin=isin_normalized,
            current_value=str(position_value_data.current_value),
        )

        return position_value


def get_position_value(db: Session, isin: str) -> PositionValue:
    """
    Get a position value by ISIN.

    Args:
        db: Database session
        isin: ISIN code

    Returns:
        Position value

    Raises:
        PositionValueNotFoundError: If position value not found
    """
    isin_normalized = isin.upper()

    position_value = db.query(PositionValue).filter(
        PositionValue.isin == isin_normalized
    ).first()

    if not position_value:
        raise PositionValueNotFoundError(isin_normalized)

    return position_value


def get_all_position_values(db: Session) -> list[PositionValue]:
    """
    Get all position values.

    Args:
        db: Database session

    Returns:
        List of all position values ordered by ISIN
    """
    return db.query(PositionValue).order_by(PositionValue.isin.asc()).all()


def delete_position_value(db: Session, isin: str) -> None:
    """
    Delete a position value by ISIN.

    Args:
        db: Database session
        isin: ISIN code

    Raises:
        PositionValueNotFoundError: If position value not found
    """
    position_value = get_position_value(db, isin)

    # Store for audit log
    deleted_value = str(position_value.current_value)

    db.delete(position_value)
    db.commit()

    # AUDIT LOG
    log_with_context(
        logger,
        logging.INFO,
        "Position value deleted",
        operation="DELETE",
        isin=position_value.isin,
        deleted_value=deleted_value,
    )


def cleanup_orphaned_position_values(db: Session) -> dict:
    """
    Clean up all orphaned position values for closed or non-existent positions.

    This maintenance utility removes position values for:
    1. ISINs with no transactions (orphaned data)
    2. ISINs with closed positions (total_units == 0)

    Args:
        db: Database session

    Returns:
        Dictionary with cleanup statistics:
        {
            "checked": int,
            "deleted": int,
            "deleted_isins": list[str],
            "errors": list[dict]
        }
    """
    position_values = get_all_position_values(db)

    stats = {
        "checked": len(position_values),
        "deleted": 0,
        "deleted_isins": [],
        "errors": []
    }

    log_with_context(
        logger,
        logging.INFO,
        "Starting position value cleanup",
        total_position_values=len(position_values),
    )

    for pv in position_values:
        try:
            # Calculate current position state
            cost_basis = cost_basis_service.calculate_cost_basis(db, pv.isin)

            # Delete if no transactions or position closed
            should_delete = (
                cost_basis is None or  # No transactions
                cost_basis.total_units == 0  # Position closed
            )

            if should_delete:
                delete_position_value(db, pv.isin)
                stats["deleted"] += 1
                stats["deleted_isins"].append(pv.isin)

        except Exception as e:
            # LOG ERROR - previously not logged
            error_info = {
                "isin": pv.isin,
                "error": str(e)
            }
            stats["errors"].append(error_info)

            log_with_context(
                logger,
                logging.ERROR,
                "Error during position value cleanup",
                isin=pv.isin,
                error_type=type(e).__name__,
                error_message=str(e),
            )

    log_with_context(
        logger,
        logging.INFO,
        "Position value cleanup completed",
        checked=stats["checked"],
        deleted=stats["deleted"],
        errors_count=len(stats["errors"]),
    )

    return stats
