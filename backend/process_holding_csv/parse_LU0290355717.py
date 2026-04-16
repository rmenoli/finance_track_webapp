"""DWS Xtrackers Eurozone Government Bond holdings parser."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import openpyxl

from .base import HoldingRow, standardize_country, write_csv

ETF_ISIN = "LU0290355717"
HEADER_ROW = 3  # 0-indexed


def parse(filepath: Path) -> list[HoldingRow]:
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active
    grouped: dict[tuple[str, str, str, str], float] = defaultdict(float)
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i <= HEADER_ROW:
            continue
        if row[1] is None:
            continue
        try:
            weight = float(row[10])
        except (ValueError, TypeError):
            continue
        country = standardize_country(str(row[3]).strip())
        currency = str(row[4]).strip()
        key = (f"{country} Bond", country, "Bond-Gov", currency)
        grouped[key] += weight
    wb.close()
    return [
        HoldingRow(ticker=t, country=c, sector=s, currency=cur, weight_pct=w)
        for (t, c, s, cur), w in grouped.items()
    ]


if __name__ == "__main__":
    input_path = Path(sys.argv[1])
    holdings = parse(input_path)
    output_path = input_path.parent / f"{ETF_ISIN}.csv"
    write_csv(holdings, output_path)
    print(f"Wrote {len(holdings)} rows to {output_path}")
