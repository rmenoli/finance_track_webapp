"""Service for loading and querying ETF constituent breakdowns from CSV files."""

import csv
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)

_ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


class WeightEntry(TypedDict):
    name: str
    weight_pct: float


class BreakdownResult(TypedDict):
    by_country: list[WeightEntry]
    by_sector: list[WeightEntry]
    by_currency: list[WeightEntry]
    by_ticker: list[WeightEntry]


_cache: dict[str, BreakdownResult] = {}


def _aggregate_and_sort(rows: list[dict[str, str]], key: str) -> list[WeightEntry]:
    """Aggregate weight_pct by a given key and return sorted descending."""
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        totals[row[key]] += float(row["weight_pct"])
    return sorted(
        [{"name": name, "weight_pct": weight} for name, weight in totals.items()],
        key=lambda e: e["weight_pct"],
        reverse=True,
    )


def load_breakdowns(data_dir: Path) -> None:
    """Load all ISIN CSV files from data_dir into the in-memory cache."""
    global _cache
    new_cache: dict[str, BreakdownResult] = {}

    for csv_path in data_dir.glob("*.csv"):
        isin = csv_path.stem
        if not _ISIN_PATTERN.match(isin):
            continue

        with open(csv_path, newline="") as f:
            rows = list(csv.DictReader(f))

        if not rows:
            continue

        new_cache[isin] = {
            "by_country": _aggregate_and_sort(rows, "country"),
            "by_sector": _aggregate_and_sort(rows, "sector"),
            "by_currency": _aggregate_and_sort(rows, "currency"),
            "by_ticker": _aggregate_and_sort(rows, "ticker"),
        }

    _cache = new_cache
    logger.info("Loaded ETF breakdowns for %d ISINs", len(_cache))


def get_all_breakdowns() -> dict[str, BreakdownResult]:
    """Return all available breakdowns keyed by ISIN."""
    return dict(_cache)


def get_breakdown(isin: str) -> BreakdownResult | None:
    """Return the breakdown for a given ISIN, or None if not available."""
    return _cache.get(isin)


def get_available_isins() -> list[str]:
    """Return a sorted list of ISINs with available breakdown data."""
    return sorted(_cache.keys())
