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


@router.delete(
    "/{position_value_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete position value by ID",
    description="Delete a position value by its ID",
)
def delete_position_value_by_id(
    position_value_id: int = Path(..., description="Position value ID"),
    db: Session = Depends(get_db),
) -> None:
    """Delete a position value by ID."""
    position_value_service.delete_position_value_by_id(db, position_value_id)
