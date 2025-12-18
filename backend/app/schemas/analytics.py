from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CostBasisResponse(BaseModel):
    """Schema for cost basis calculation response."""

    isin: str = Field(..., description="ISIN code")
    total_units: Decimal = Field(..., description="Total units currently held")
    total_cost_without_fees: Decimal = Field(
        ..., description="Total cost without fees (sum of the buy costs)"
    )
    total_gains_without_fees: Decimal = Field(
        ..., description="Total gains without fees (sum of the revenue from sells)"
    )
    total_fees: Decimal = Field(..., description="Total fees")
    transactions_count: int = Field(..., description="Number of transactions")

    model_config = ConfigDict(from_attributes=True)


class PortfolioSummaryResponse(BaseModel):
    """Schema for overall portfolio summary."""

    total_invested: Decimal = Field(..., description="Total amount invested (buys)")
    total_fees: Decimal = Field(..., description="Total fees paid")
    holdings: list[CostBasisResponse] = Field(..., description="Current holdings")

    model_config = ConfigDict(from_attributes=True)
