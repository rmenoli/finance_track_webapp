from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field


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

    # Position value and P/L fields (None if position value not available)
    current_value: Optional[Decimal] = Field(
        None, description="Current market value of the position"
    )
    absolute_pl_without_fees: Optional[Decimal] = Field(
        None, description="Absolute profit/loss without fees"
    )
    percentage_pl_without_fees: Optional[Decimal] = Field(
        None, description="Percentage profit/loss without fees"
    )
    absolute_pl_with_fees: Optional[Decimal] = Field(
        None, description="Absolute profit/loss with fees"
    )
    percentage_pl_with_fees: Optional[Decimal] = Field(
        None, description="Percentage profit/loss with fees"
    )

    @computed_field
    @property
    def net_buy_in_cost(self) -> Decimal:
        """Calculate net buy-in cost (total_cost - total_gains, both without fees)."""
        return self.total_cost_without_fees - self.total_gains_without_fees

    @computed_field
    @property
    def net_buy_in_cost_per_unit(self) -> Optional[Decimal]:
        """Calculate net buy-in cost per unit. Returns None if no units held."""
        if self.total_units > 0:
            return self.net_buy_in_cost / self.total_units
        return None

    @computed_field
    @property
    def current_price_per_unit(self) -> Optional[Decimal]:
        """Calculate current price per unit. Returns None if no current value or no units."""
        if self.current_value and self.total_units > 0:
            return self.current_value / self.total_units
        return None

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
