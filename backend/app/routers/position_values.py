"""Position values API router."""

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.position_value import (
    PositionValueCreate,
    PositionValueListResponse,
    PositionValueResponse,
)
from app.services import position_value_service

router = APIRouter(prefix="/position-values", tags=["position-values"])


@router.post(
    "",
    response_model=PositionValueResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update position value",
    description="Create a new position value or update existing one (UPSERT by ISIN)",
)
def upsert_position_value(
    position_value: PositionValueCreate,
    db: Session = Depends(get_db),
) -> PositionValueResponse:
    """Create or update a position value."""
    result = position_value_service.upsert_position_value(db, position_value)
    return PositionValueResponse.model_validate(result)


@router.get(
    "",
    response_model=PositionValueListResponse,
    summary="List all position values",
    description="Get all stored position values",
)
def list_position_values(
    db: Session = Depends(get_db),
) -> PositionValueListResponse:
    """List all position values."""
    position_values = position_value_service.get_all_position_values(db)

    return PositionValueListResponse(
        position_values=[
            PositionValueResponse.model_validate(pv) for pv in position_values
        ],
        total=len(position_values),
    )


@router.get(
    "/{isin}",
    response_model=PositionValueResponse,
    summary="Get position value by ISIN",
    description="Retrieve a specific position value by ISIN",
)
def get_position_value(
    isin: str = Path(..., min_length=1, max_length=12, description="ISIN code"),
    db: Session = Depends(get_db),
) -> PositionValueResponse:
    """Get a position value by ISIN."""
    position_value = position_value_service.get_position_value(db, isin)
    return PositionValueResponse.model_validate(position_value)


@router.delete(
    "/{isin}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete position value",
    description="Delete a position value by ISIN",
)
def delete_position_value(
    isin: str = Path(..., min_length=1, max_length=12, description="ISIN code"),
    db: Session = Depends(get_db),
) -> None:
    """Delete a position value."""
    position_value_service.delete_position_value(db, isin)


@router.post(
    "/cleanup",
    status_code=status.HTTP_200_OK,
    summary="Clean up orphaned position values",
    description="Remove position values for closed or non-existent positions (maintenance utility)",
)
def cleanup_orphaned_position_values_endpoint(
    db: Session = Depends(get_db),
) -> dict:
    """
    Clean up orphaned position values.

    Returns statistics about the cleanup operation.
    """
    return position_value_service.cleanup_orphaned_position_values(db)
