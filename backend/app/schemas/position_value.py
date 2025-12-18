"""Position value schemas for validation and serialization."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PositionValueBase(BaseModel):
    """Base schema for position value data."""

    isin: str = Field(..., min_length=1, max_length=12, description="ISIN code")
    current_value: Decimal = Field(..., gt=0, description="Current total position value")


class PositionValueCreate(BaseModel):
    """Schema for creating/updating a position value (UPSERT operation)."""

    isin: str = Field(..., min_length=1, max_length=12, description="ISIN code")
    current_value: Decimal = Field(..., gt=0, description="Current total position value")


class PositionValueResponse(PositionValueBase):
    """Schema for position value responses."""

    id: int = Field(..., description="Position value ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class PositionValueListResponse(BaseModel):
    """Schema for list of position values."""

    position_values: list[PositionValueResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
