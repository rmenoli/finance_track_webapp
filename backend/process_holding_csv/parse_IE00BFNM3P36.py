"""iShares MSCI World Small Cap UCITS ETF (WSML) holdings parser.

Source: iShares Italian CSV export. File starts with a date line and a blank
line before the actual header row; fields use Italian decimal format (comma
as decimal separator, dot as thousands separator).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from .base import HoldingRow, standardize_country, standardize_sector, write_csv

ETF_ISIN = "IE00BFNM3P36"
SKIP_ROWS = 2  # date line + blank line before header


def _parse_italian_pct(value: str) -> float:
    """Parse Italian decimal percentage string, e.g. '1,17' -> 0.0117."""
    cleaned = value.strip().replace(".", "").replace(",", ".")
    return float(cleaned) / 100


def parse(filepath: Path) -> list[HoldingRow]:
    """Parse an iShares Italian CSV export and return normalised holding rows."""
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        for _ in range(SKIP_ROWS):
            next(f)
        reader = csv.DictReader(f)
        rows: list[HoldingRow] = []
        for row in reader:
            ticker = row.get("Ticker dell'emittente", "").strip()
            if not ticker:
                continue
            country = standardize_country(row.get("Area Geografica", "").strip())
            sector = standardize_sector(row.get("Settore", "").strip())
            currency = row.get("Valuta di mercato", "").strip()
            weight_pct = _parse_italian_pct(row.get("Ponderazione (%)", "0"))
            rows.append(HoldingRow(ticker=ticker, country=country, sector=sector, currency=currency, weight_pct=weight_pct))
    return rows


if __name__ == "__main__":
    input_path = Path(sys.argv[1])
    holdings = parse(input_path)
    output_path = input_path.parent / f"{ETF_ISIN}.csv"
    write_csv(holdings, output_path)
    print(f"Wrote {len(holdings)} rows to {output_path}")
