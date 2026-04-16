"""iShares MSCI World Small Cap (WSML) holdings parser."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from .base import HoldingRow, standardize_country, standardize_sector, write_csv

ETF_ISIN = "IE00BF4RFH31"


def _parse_italian_pct(value: str) -> float:
    """Parse Italian percentage like '1,17' -> 0.0117."""
    return float(value.replace(".", "").replace(",", ".")) / 100


def parse(filepath: Path) -> list[HoldingRow]:
    rows: list[HoldingRow] = []
    with open(filepath, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i < 3:  # skip date, blank, header
                continue
            if len(row) < 12:
                continue
            ticker = row[0].strip()
            if not ticker:
                continue
            rows.append(
                HoldingRow(
                    ticker=ticker,
                    country=standardize_country(row[9].strip()),
                    sector=standardize_sector(row[2].strip()),
                    currency=row[11].strip(),
                    weight_pct=_parse_italian_pct(row[5]),
                )
            )
    return rows


if __name__ == "__main__":
    input_path = Path(sys.argv[1])
    holdings = parse(input_path)
    output_path = input_path.parent / f"{ETF_ISIN}.csv"
    write_csv(holdings, output_path)
    print(f"Wrote {len(holdings)} rows to {output_path}")
