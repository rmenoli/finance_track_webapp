"""User setting schemas for validation and serialization."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ExchangeRateUpdateRequest(BaseModel):
    """Schema for updating exchange rate setting."""

    exchange_rate: Decimal = Field(
        ..., gt=0, decimal_places=2, description="CZK per 1 EUR (e.g., 25.00)"
    )


class ExchangeRateResponse(BaseModel):
    """Schema for exchange rate response."""

    exchange_rate: Decimal = Field(..., description="CZK per 1 EUR")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class ExpectedReturnUpdateRequest(BaseModel):
    """Schema for updating expected return setting."""

    expected_return: Decimal = Field(
        ...,
        ge=0,
        le=100,
        decimal_places=2,
        description="Expected return percentage (e.g., 7.50 for 7.50%)",
    )


class ExpectedReturnResponse(BaseModel):
    """Schema for expected return response."""

    expected_return: Decimal = Field(..., description="Expected return percentage")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)
