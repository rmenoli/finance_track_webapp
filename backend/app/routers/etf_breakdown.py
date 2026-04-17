"""API routes for ETF holding breakdown data."""

from fastapi import APIRouter, HTTPException

from app.schemas.etf_breakdown import (
    AllETFBreakdownsResponse,
    AvailableETFsResponse,
    ETFBreakdownResponse,
)
from app.services import etf_breakdown_service

router = APIRouter(prefix="/etf-breakdown", tags=["etf-breakdown"])


@router.get(
    "/",
    response_model=AvailableETFsResponse,
    summary="List available ETF breakdowns",
)
def list_available_etfs() -> AvailableETFsResponse:
    """Return ISINs for which holding breakdown data is available."""
    return AvailableETFsResponse(isins=etf_breakdown_service.get_available_isins())


@router.get(
    "/all",
    response_model=AllETFBreakdownsResponse,
    summary="Get all ETF holding breakdowns",
)
def get_all_etf_breakdowns() -> AllETFBreakdownsResponse:
    """Return country, sector, currency and ticker breakdown for all available ETFs."""
    all_data = etf_breakdown_service.get_all_breakdowns()
    return AllETFBreakdownsResponse(
        breakdowns={
            isin: ETFBreakdownResponse(isin=isin, **breakdown)
            for isin, breakdown in all_data.items()
        }
    )


@router.get(
    "/{isin}",
    response_model=ETFBreakdownResponse,
    summary="Get ETF holding breakdown",
)
def get_etf_breakdown(isin: str) -> ETFBreakdownResponse:
    """Return country, sector, and currency breakdown for one ETF."""
    breakdown = etf_breakdown_service.get_breakdown(isin)
    if breakdown is None:
        raise HTTPException(status_code=404, detail=f"No breakdown data for ISIN {isin}")
    return ETFBreakdownResponse(isin=isin, **breakdown)
