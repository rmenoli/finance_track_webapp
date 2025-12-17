from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analytics import (
    CostBasisResponse,
    HoldingResponse,
    PortfolioSummaryResponse,
    RealizedGainResponse,
)
from app.services import cost_basis_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/cost-basis/{isin}",
    response_model=CostBasisResponse,
    summary="Get cost basis for specific ISIN",
    description="Calculate cost basis for a specific ISIN using average cost method",
)
def get_cost_basis(
    isin: str,
    as_of_date: Optional[date] = Query(
        None, description="Calculate as of specific date"
    ),
    db: Session = Depends(get_db),
) -> CostBasisResponse:
    """Get cost basis for a specific ISIN."""
    cost_basis = cost_basis_service.calculate_cost_basis(db, isin, as_of_date)

    if not cost_basis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No transactions found for ISIN: {isin}",
        )

    return cost_basis


@router.get(
    "/cost-basis",
    response_model=list[CostBasisResponse],
    summary="Get cost basis for all holdings",
    description="Calculate cost basis for all ISINs in the portfolio",
)
def get_all_cost_bases(
    as_of_date: Optional[date] = Query(
        None, description="Calculate as of specific date"
    ),
    db: Session = Depends(get_db),
) -> list[CostBasisResponse]:
    """Get cost basis for all ISINs."""
    # Get all unique ISINs
    from app.models.transaction import Transaction

    isins = db.query(Transaction.isin).distinct().all()

    cost_bases = []
    for (isin,) in isins:
        cost_basis = cost_basis_service.calculate_cost_basis(db, isin, as_of_date)
        if cost_basis and cost_basis.total_units > 0:
            cost_bases.append(cost_basis)

    return cost_bases


@router.get(
    "/holdings",
    response_model=list[HoldingResponse],
    summary="Get current holdings",
    description="Get current holdings for all ISINs in the portfolio",
)
def get_holdings(
    db: Session = Depends(get_db),
) -> list[HoldingResponse]:
    """Get current holdings."""
    return cost_basis_service.calculate_current_holdings(db)


@router.get(
    "/realized-gains",
    response_model=list[RealizedGainResponse],
    summary="Get realized gains",
    description="Calculate realized gains/losses from SELL transactions",
)
def get_realized_gains(
    isin: Optional[str] = Query(None, description="Filter by ISIN"),
    db: Session = Depends(get_db),
) -> list[RealizedGainResponse]:
    """Get realized gains from sell transactions."""
    return cost_basis_service.calculate_realized_gains(db, isin)


@router.get(
    "/portfolio-summary",
    response_model=PortfolioSummaryResponse,
    summary="Get portfolio summary",
    description="Get overall portfolio summary with holdings, investments, and realized gains",
)
def get_portfolio_summary(
    db: Session = Depends(get_db),
) -> PortfolioSummaryResponse:
    """Get overall portfolio summary."""
    return cost_basis_service.get_portfolio_summary(db)
