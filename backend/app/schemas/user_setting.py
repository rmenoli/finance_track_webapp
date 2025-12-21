"""User setting schemas for validation and serialization."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ExchangeRateUpdateRequest(BaseModel):
    """Schema for updating exchange rate setting."""

    exchange_rate: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="CZK per 1 EUR (e.g., 25.00)"
    )


class ExchangeRateResponse(BaseModel):
    """Schema for exchange rate response."""

    exchange_rate: Decimal = Field(..., description="CZK per 1 EUR")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)
