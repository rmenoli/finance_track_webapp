from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.constants import TransactionType
from app.models.transaction import Transaction
from app.schemas.analytics import (
    CostBasisResponse,
    PortfolioSummaryResponse,
)
from app.services import position_value_service


def calculate_cost_basis(
    db: Session, isin: str, as_of_date: Optional[date] = None
) -> Optional[CostBasisResponse]:
    """
    Calculate cost basis for a specific ISIN using average cost method.

    Args:
        db: Database session
        isin: ISIN code
        as_of_date: Calculate as of specific date (None for current)

    Returns:
        Cost basis response or None if no transactions found
    """
    query = db.query(Transaction).filter(Transaction.isin == isin.upper())

    if as_of_date:
        query = query.filter(Transaction.date <= as_of_date)

    transactions = query.order_by(Transaction.date.asc()).all()

    if not transactions:
        return None

    total_units = Decimal("0")

    sum_costs_without_fees = Decimal("0")
    sum_gains_without_fees = Decimal("0")

    total_fees = Decimal("0")
    transaction_count = 0

    for txn in transactions:
        if txn.transaction_type == TransactionType.BUY:
            # Add cost including fee
            without_fee_cost = txn.price_per_unit * txn.units
            sum_costs_without_fees += without_fee_cost

            total_fees += txn.fee
            total_units += txn.units

            transaction_count += 1
        elif txn.transaction_type == TransactionType.SELL:
            # Calculate proportion of cost basis to remove
            gaining_wihtout_fees = txn.price_per_unit * txn.units
            sum_gains_without_fees = sum_gains_without_fees + gaining_wihtout_fees

            total_fees += txn.fee
            total_units -= txn.units

            transaction_count += 1

    return CostBasisResponse(
        isin=isin.upper(),
        total_units=total_units,
        total_cost_without_fees=sum_costs_without_fees,
        total_gains_without_fees=sum_gains_without_fees,
        total_fees=total_fees,
        transactions_count=transaction_count,
        current_value=None,  # Will be set by caller if available
        absolute_pl_without_fees=None,
        percentage_pl_without_fees=None,
        absolute_pl_with_fees=None,
        percentage_pl_with_fees=None,
    )


def calculate_current_holdings_and_closed_positions(
    db: Session, position_values_map: dict[str, Decimal]
) -> tuple[list[CostBasisResponse], list[CostBasisResponse]]:
    """
    Calculate current holdings and closed positions for all ISINs with P/L calculations.

    Args:
        db: Database session
        position_values_map: Dictionary mapping ISIN to current position value

    Returns:
        Tuple of (holdings, closed_positions)
    """
    # Get all unique ISINs
    isins = db.query(Transaction.isin).distinct().all()

    holdings = []
    closed_positions = []
    for (isin,) in isins:
        cost_basis = calculate_cost_basis(db, isin)
        if cost_basis:
            # Get position value for this ISIN
            current_value = position_values_map.get(isin.upper())

            # Calculate P/L if position value is available and position is open
            if current_value is not None and cost_basis.total_units > 0:
                # P/L without fees
                total_cost_without_fees = (
                    cost_basis.total_cost_without_fees - cost_basis.total_gains_without_fees
                )
                absolute_pl_without_fees = current_value - total_cost_without_fees
                percentage_pl_without_fees = (
                    (absolute_pl_without_fees / total_cost_without_fees * Decimal("100"))
                    if total_cost_without_fees > 0
                    else Decimal("0")
                )

                # P/L with fees
                total_cost_with_fees = total_cost_without_fees + cost_basis.total_fees
                absolute_pl_with_fees = current_value - total_cost_with_fees
                percentage_pl_with_fees = (
                    (absolute_pl_with_fees / total_cost_with_fees * Decimal("100"))
                    if total_cost_with_fees > 0
                    else Decimal("0")
                )

                # Update cost basis with P/L values
                cost_basis.current_value = current_value
                cost_basis.absolute_pl_without_fees = absolute_pl_without_fees
                cost_basis.percentage_pl_without_fees = percentage_pl_without_fees
                cost_basis.absolute_pl_with_fees = absolute_pl_with_fees
                cost_basis.percentage_pl_with_fees = percentage_pl_with_fees

            # For closed positions, calculate realized P/L
            elif cost_basis.total_units == 0:
                # Realized P/L without fees
                absolute_pl_without_fees = (
                    cost_basis.total_gains_without_fees - cost_basis.total_cost_without_fees
                )
                percentage_pl_without_fees = (
                    (absolute_pl_without_fees / cost_basis.total_cost_without_fees * Decimal("100"))
                    if cost_basis.total_cost_without_fees > 0
                    else Decimal("0")
                )

                # Realized P/L with fees
                absolute_pl_with_fees = absolute_pl_without_fees - cost_basis.total_fees
                total_cost_with_fees = cost_basis.total_cost_without_fees + cost_basis.total_fees
                percentage_pl_with_fees = (
                    (absolute_pl_with_fees / total_cost_with_fees * Decimal("100"))
                    if total_cost_with_fees > 0
                    else Decimal("0")
                )

                # Update with realized P/L
                cost_basis.current_value = Decimal("0")  # Closed position
                cost_basis.absolute_pl_without_fees = absolute_pl_without_fees
                cost_basis.percentage_pl_without_fees = percentage_pl_without_fees
                cost_basis.absolute_pl_with_fees = absolute_pl_with_fees
                cost_basis.percentage_pl_with_fees = percentage_pl_with_fees

            # Categorize as holding or closed position
            if cost_basis.total_units > 0:
                holdings.append(cost_basis)
            elif cost_basis.total_units == 0:
                closed_positions.append(cost_basis)

    return holdings, closed_positions


def get_portfolio_summary(db: Session) -> PortfolioSummaryResponse:
    """
    Get overall portfolio summary with P/L calculations.

    Args:
        db: Database session

    Returns:
        Portfolio summary with calculated P/L for each holding
    """
    # Fetch all position values and create a map for efficient lookup
    position_values = position_value_service.get_all_position_values(db)
    position_values_map = {pv.isin.upper(): pv.current_value for pv in position_values}

    # Calculate current holdings and closed positions with P/L
    holdings, closed_positions = calculate_current_holdings_and_closed_positions(
        db, position_values_map
    )

    # Calculate total invested (all BUY transactions)
    buy_transactions = (
        db.query(Transaction).filter(Transaction.transaction_type == TransactionType.BUY).all()
    )
    total_invested = sum((txn.price_per_unit * txn.units) for txn in buy_transactions)

    # Calculate total amount withdrawn (all SELL transactions)
    sell_transactions = (
        db.query(Transaction).filter(Transaction.transaction_type == TransactionType.SELL).all()
    )
    total_withdrawn = sum((txn.price_per_unit * txn.units) for txn in sell_transactions)

    # Calculate total fees
    all_transactions = db.query(Transaction).all()
    total_fees = sum(txn.fee for txn in all_transactions)

    # Calculate sum of all position values
    total_current_portfolio_invested_value = (
        sum(pv.current_value for pv in position_values) if position_values else Decimal("0")
    )

    # Calculate total profit/loss
    total_profit_loss = (
        total_current_portfolio_invested_value + total_withdrawn - total_fees - total_invested
    )

    return PortfolioSummaryResponse(
        total_invested=total_invested,
        total_withdrawn=total_withdrawn,
        total_fees=total_fees,
        total_current_portfolio_invested_value=total_current_portfolio_invested_value,
        total_profit_loss=total_profit_loss,
        holdings=holdings,
        closed_positions=closed_positions,
    )
