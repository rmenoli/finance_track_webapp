from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class HoldingResponse(BaseModel):
    """Schema for current holdings of a specific ISIN."""

    isin: str = Field(..., description="ISIN code")
    units: Decimal = Field(..., description="Total units currently held")
    average_cost_per_unit: Decimal = Field(
        ..., description="Average cost per unit (including fees)"
    )
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
    average_cost_per_unit: Decimal = Field(
        ..., description="Average cost per unit (including fees)"
    )
    transactions_count: int = Field(..., description="Number of transactions")
    current_market_value: Optional[Decimal] = Field(
        None, description="Current market value (if price is known)"
    )
    unrealized_gain_loss: Optional[Decimal] = Field(
        None, description="Unrealized gain/loss (if current price is known)"
    )

    model_config = ConfigDict(from_attributes=True)


class RealizedGainResponse(BaseModel):
    """Schema for realized gains from sell transactions."""

    isin: str = Field(..., description="ISIN code")
    total_realized_gain: Decimal = Field(
        ..., description="Total realized gain/loss from all sell transactions"
    )
    sell_transactions_count: int = Field(
        ..., description="Number of sell transactions"
    )

    model_config = ConfigDict(from_attributes=True)


class PortfolioSummaryResponse(BaseModel):
    """Schema for overall portfolio summary."""

    total_invested: Decimal = Field(..., description="Total amount invested (buys)")
    total_fees: Decimal = Field(..., description="Total fees paid")
    holdings: list[HoldingResponse] = Field(..., description="Current holdings")
    realized_gains: Decimal = Field(
        ..., description="Total realized gains from sells"
    )
    realized_losses: Decimal = Field(
        ..., description="Total realized losses from sells"
    )
    net_realized_gains: Decimal = Field(
        ..., description="Net realized gains/losses"
    )
    unique_isins: int = Field(..., description="Number of unique ISINs")

    model_config = ConfigDict(from_attributes=True)
