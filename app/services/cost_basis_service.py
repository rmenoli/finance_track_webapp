from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.constants import TransactionType
from app.models.transaction import Transaction
from app.schemas.analytics import (
    CostBasisResponse,
    HoldingResponse,
    PortfolioSummaryResponse,
    RealizedGainResponse,
)


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
    total_cost = Decimal("0")
    transaction_count = 0

    for txn in transactions:
        if txn.transaction_type == TransactionType.BUY:
            # Add cost including fee
            cost = (txn.price_per_unit * txn.units) + txn.fee
            total_cost += cost
            total_units += txn.units
            transaction_count += 1
        elif txn.transaction_type == TransactionType.SELL:
            if total_units > 0:
                # Calculate proportion of cost basis to remove
                proportion = txn.units / total_units
                cost_removed = total_cost * proportion
                total_cost -= cost_removed
                total_units -= txn.units
            transaction_count += 1

    if total_units <= 0:
        # All positions sold
        return CostBasisResponse(
            isin=isin.upper(),
            total_units=Decimal("0"),
            total_cost=Decimal("0"),
            average_cost_per_unit=Decimal("0"),
            transactions_count=transaction_count,
        )

    average_cost = total_cost / total_units if total_units > 0 else Decimal("0")

    return CostBasisResponse(
        isin=isin.upper(),
        total_units=total_units,
        total_cost=total_cost,
        average_cost_per_unit=average_cost,
        transactions_count=transaction_count,
    )


def calculate_current_holdings(db: Session) -> list[HoldingResponse]:
    """
    Calculate current holdings for all ISINs.

    Args:
        db: Database session

    Returns:
        List of holdings
    """
    # Get all unique ISINs
    isins = db.query(Transaction.isin).distinct().all()

    holdings = []
    for (isin,) in isins:
        cost_basis = calculate_cost_basis(db, isin)
        if cost_basis and cost_basis.total_units > 0:
            holdings.append(
                HoldingResponse(
                    isin=cost_basis.isin,
                    units=cost_basis.total_units,
                    average_cost_per_unit=cost_basis.average_cost_per_unit,
                    total_cost=cost_basis.total_cost,
                )
            )

    return holdings


def calculate_realized_gains(
    db: Session, isin: Optional[str] = None
) -> list[RealizedGainResponse]:
    """
    Calculate realized gains from SELL transactions.

    Args:
        db: Database session
        isin: Optional ISIN to filter by

    Returns:
        List of realized gains by ISIN
    """
    query = db.query(Transaction.isin).distinct()
    if isin:
        query = query.filter(Transaction.isin == isin.upper())

    isins = query.all()
    realized_gains = []

    for (current_isin,) in isins:
        transactions = (
            db.query(Transaction)
            .filter(Transaction.isin == current_isin)
            .order_by(Transaction.date.asc())
            .all()
        )

        total_units = Decimal("0")
        total_cost = Decimal("0")
        total_realized_gain = Decimal("0")
        sell_count = 0

        for txn in transactions:
            if txn.transaction_type == TransactionType.BUY:
                cost = (txn.price_per_unit * txn.units) + txn.fee
                total_cost += cost
                total_units += txn.units
            elif txn.transaction_type == TransactionType.SELL:
                if total_units > 0:
                    # Calculate average cost per unit before this sale
                    avg_cost = total_cost / total_units

                    # Calculate cost basis for units sold
                    cost_basis = avg_cost * txn.units

                    # Calculate net proceeds (gross proceeds - fee)
                    gross_proceeds = txn.price_per_unit * txn.units
                    net_proceeds = gross_proceeds - txn.fee

                    # Calculate realized gain/loss
                    realized_gain = net_proceeds - cost_basis
                    total_realized_gain += realized_gain

                    # Reduce holdings proportionally
                    proportion = txn.units / total_units
                    cost_removed = total_cost * proportion
                    total_cost -= cost_removed
                    total_units -= txn.units

                    sell_count += 1

        if sell_count > 0:
            realized_gains.append(
                RealizedGainResponse(
                    isin=current_isin,
                    total_realized_gain=total_realized_gain,
                    sell_transactions_count=sell_count,
                )
            )

    return realized_gains


def get_portfolio_summary(db: Session) -> PortfolioSummaryResponse:
    """
    Get overall portfolio summary.

    Args:
        db: Database session

    Returns:
        Portfolio summary
    """
    # Calculate current holdings
    holdings = calculate_current_holdings(db)

    # Calculate total invested (all BUY transactions)
    buy_transactions = (
        db.query(Transaction)
        .filter(Transaction.transaction_type == TransactionType.BUY)
        .all()
    )
    total_invested = sum(
        (txn.price_per_unit * txn.units) for txn in buy_transactions
    )

    # Calculate total fees
    all_transactions = db.query(Transaction).all()
    total_fees = sum(txn.fee for txn in all_transactions)

    # Calculate realized gains
    realized_gains_list = calculate_realized_gains(db)
    total_realized_gains = Decimal("0")
    total_realized_losses = Decimal("0")

    for rg in realized_gains_list:
        if rg.total_realized_gain > 0:
            total_realized_gains += rg.total_realized_gain
        else:
            total_realized_losses += rg.total_realized_gain

    net_realized_gains = total_realized_gains + total_realized_losses

    # Count unique ISINs with current holdings
    unique_isins = len(holdings)

    return PortfolioSummaryResponse(
        total_invested=total_invested,
        total_fees=total_fees,
        holdings=holdings,
        realized_gains=total_realized_gains,
        realized_losses=total_realized_losses,
        net_realized_gains=net_realized_gains,
        unique_isins=unique_isins,
    )
