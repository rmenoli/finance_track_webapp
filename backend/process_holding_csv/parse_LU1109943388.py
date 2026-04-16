"""DWS Xtrackers EUR High Yield Corporate Bond holdings parser."""

from __future__ import annotations

import sys
from pathlib import Path

import openpyxl

from .base import HoldingRow, standardize_country, write_csv

ETF_ISIN = "LU1109943388"
HEADER_ROW = 3  # 0-indexed


def parse(filepath: Path) -> list[HoldingRow]:
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active
    rows: list[HoldingRow] = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i <= HEADER_ROW:
            continue
        if row[1] is None:
            continue
        try:
            weight = float(row[10])
        except (ValueError, TypeError):
            continue
        rows.append(
            HoldingRow(
                ticker=str(row[1]).strip(),
                country=standardize_country(str(row[3]).strip()),
                sector="Bond-Corp",
                currency=str(row[4]).strip(),
                weight_pct=weight,
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
