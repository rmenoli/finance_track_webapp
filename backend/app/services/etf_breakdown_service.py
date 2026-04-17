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
_loaded: bool = False


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
    global _cache, _loaded
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
    _loaded = True
    logger.info("Loaded ETF breakdowns for %d ISINs", len(_cache))


def _download_from_s3(bucket: str, prefix: str, dest: Path) -> int:
    """Download ISIN CSV files from S3 to a local directory. Returns expected ISIN count."""
    import boto3

    s3 = boto3.client("s3")
    dest.mkdir(parents=True, exist_ok=True)

    keys_to_download: list[tuple[str, str]] = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            filename = key.rsplit("/", 1)[-1]
            isin = filename.removesuffix(".csv")
            if not filename.endswith(".csv") or not _ISIN_PATTERN.match(isin):
                continue
            keys_to_download.append((key, filename))

    for key, filename in keys_to_download:
        s3.download_file(bucket, key, str(dest / filename))

    logger.info("Downloaded %d ETF files from s3://%s/%s to %s", len(keys_to_download), bucket, prefix, dest)
    return len(keys_to_download)


def _ensure_loaded() -> None:
    """Load breakdown data on first access. Retries on failure."""
    global _loaded
    if _loaded:
        return

    from app.config import settings

    try:
        if settings.etf_data_s3_bucket:
            dest = Path("/tmp/etf_data")
            expected = _download_from_s3(settings.etf_data_s3_bucket, settings.etf_data_s3_prefix, dest)
            load_breakdowns(dest)
            if len(_cache) < expected:
                _loaded = False
                raise RuntimeError(f"Only {len(_cache)}/{expected} ISINs loaded — will retry")
        elif settings.etf_data_dir:
            load_breakdowns(Path(settings.etf_data_dir))
        else:
            logger.warning("No ETF data source configured")
    except Exception:
        logger.exception("Failed to load ETF breakdown data — will retry on next request")
        return

    _loaded = True


def get_breakdown(isin: str) -> BreakdownResult | None:
    """Return the breakdown for a given ISIN, or None if not available."""
    _ensure_loaded()
    return _cache.get(isin)


def get_available_isins() -> list[str]:
    """Return a sorted list of ISINs with available breakdown data."""
    _ensure_loaded()
    return sorted(_cache.keys())
