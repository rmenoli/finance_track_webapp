"""Vanguard FTSE All-World UCITS ETF (VWCE) holdings parser."""

from __future__ import annotations

import sys
from pathlib import Path

import openpyxl

from .base import (
    HoldingRow,
    currency_from_country,
    standardize_country,
    standardize_sector,
    write_csv,
)

ETF_ISIN = "IE00BK5BQT80"
HEADER_ROW = 6  # 0-indexed


def _parse_vanguard_pct(value: str) -> float:
    """Parse '4,1278%' -> 0.041278."""
    cleaned = value.strip().rstrip("%")
    return float(cleaned.replace(".", "").replace(",", ".")) / 100


def parse(filepath: Path) -> list[HoldingRow]:
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active
    rows: list[HoldingRow] = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i <= HEADER_ROW:
            continue
        if row[0] is None:
            continue
        ticker = str(row[0]).strip()
        if len(ticker) > 20:
            continue
        pct_str = str(row[2]) if row[2] else "0%"
        country = standardize_country(str(row[4]).strip()) if row[4] else "Unknown"
        rows.append(
            HoldingRow(
                ticker=ticker,
                country=country,
                sector=standardize_sector(str(row[3]).strip()) if row[3] else "Unknown",
                currency=currency_from_country(country),
                weight_pct=_parse_vanguard_pct(pct_str),
            )
        )
    wb.close()
    return rows


if __name__ == "__main__":
    input_path = Path(sys.argv[1])
    holdings = parse(input_path)
    output_path = input_path.parent / f"{ETF_ISIN}.csv"
    write_csv(holdings, output_path)
    print(f"Wrote {len(holdings)} rows to {output_path}")
