"""Position value service for business logic."""

from sqlalchemy.orm import Session

from app.exceptions import PositionValueNotFoundError
from app.models.position_value import PositionValue
from app.schemas.position_value import PositionValueCreate


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
        existing.current_value = position_value_data.current_value
        # updated_at will auto-update via onupdate in model
        db.commit()
        db.refresh(existing)
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
    db.delete(position_value)
    db.commit()
