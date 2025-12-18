from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analytics import PortfolioSummaryResponse
from app.services import cost_basis_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/portfolio-summary",
    response_model=PortfolioSummaryResponse,
    summary="Get portfolio summary",
    description="Get overall portfolio summary with holdings, investments, and fees",
)
def get_portfolio_summary(
    db: Session = Depends(get_db),
) -> PortfolioSummaryResponse:
    """Get overall portfolio summary."""
    return cost_basis_service.get_portfolio_summary(db)
