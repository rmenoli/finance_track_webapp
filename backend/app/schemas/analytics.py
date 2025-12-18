from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class HoldingResponse(BaseModel):
    """Schema for current holdings of a specific ISIN."""

    isin: str = Field(..., description="ISIN code")
    units: Decimal = Field(..., description="Total units currently held")
    total_cost: Decimal = Field(
        ..., description="Total cost basis (including all fees)"
    )

    model_config = ConfigDict(from_attributes=True)


class CostBasisResponse(BaseModel):
    """Schema for cost basis calculation response."""

    isin: str = Field(..., description="ISIN code")
    total_units: Decimal = Field(..., description="Total units currently held")
    total_cost: Decimal = Field(
        ..., description="Total cost basis (including all fees)"
    )
    transactions_count: int = Field(..., description="Number of transactions")

    model_config = ConfigDict(from_attributes=True)


class PortfolioSummaryResponse(BaseModel):
    """Schema for overall portfolio summary."""

    total_invested: Decimal = Field(..., description="Total amount invested (buys)")
    total_fees: Decimal = Field(..., description="Total fees paid")
    holdings: list[HoldingResponse] = Field(..., description="Current holdings")

    model_config = ConfigDict(from_attributes=True)
