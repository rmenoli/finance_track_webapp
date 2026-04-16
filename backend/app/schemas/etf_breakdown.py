"""Pydantic schemas for ETF breakdown API responses."""

from pydantic import BaseModel, Field


class BreakdownEntry(BaseModel):
    """A single entry in a breakdown (e.g. one country and its weight)."""

    name: str = Field(..., description="Category name (country, sector, or currency)")
    weight_pct: float = Field(..., description="Weight as decimal (e.g. 0.04 = 4%)")


class ETFBreakdownResponse(BaseModel):
    """Breakdown of an ETF's holdings by country, sector, and currency."""

    isin: str
    by_country: list[BreakdownEntry]
    by_sector: list[BreakdownEntry]
    by_currency: list[BreakdownEntry]
    by_ticker: list[BreakdownEntry]


class AvailableETFsResponse(BaseModel):
    """List of ISINs with available breakdown data."""

    isins: list[str]
