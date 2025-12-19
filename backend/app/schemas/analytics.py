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
    total_withdrawn: Decimal = Field(..., description="Total amount withdrawn (sells)")
    total_fees: Decimal = Field(..., description="Total fees paid")
    total_current_portfolio_invested_value: Decimal = Field(
        ..., description="Sum of all current position values"
    )
    total_profit_loss: Decimal = Field(
        ..., description="Total profit/loss (current value + withdrawn - fees - invested)"
    )
    holdings: list[CostBasisResponse] = Field(..., description="Current holdings")
    closed_positions: list[CostBasisResponse] = Field(
        ..., description="Closed positions with zero units held"
    )

    model_config = ConfigDict(from_attributes=True)
