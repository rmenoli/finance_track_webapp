import tempfile
from pathlib import Path

import openpyxl

from process_holding_csv.parse_LU1109943388 import parse


def _create_test_xlsx(path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "2026-04-13"
    ws.append([None] * 11)  # blank row
    ws.append(["Disclaimer text"] + [None] * 10)
    ws.append([None] * 11)  # blank row
    ws.append([None, "Name", "ISIN", "Country", "Currency", "Exchange",
               "Type of Security", "Rating", "Primary Listing",
               "Industry Classification", "Weighting"])
    ws.append([1, "VMED O2 UK FINANCING I PLC", "XS2796600307", "Regno Unito",
               "EUR", "-", "Obbligazioni", "-", "-", "sconosciuta", 0.005])
    ws.append([2, "FIBERCOP SPA", "XS3104481257", "Italia", "EUR", "-",
               "Obbligazioni", "-", "-", "sconosciuta", 0.0035])
    wb.save(path)


class TestParseDwsHighYield:
    def test_parses_sample_rows(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            path = Path(f.name)
        _create_test_xlsx(path)

        rows = parse(path)
        path.unlink()

        assert len(rows) == 2
        assert rows[0].ticker == "VMED O2 UK FINANCING I PLC"
        assert rows[0].country == "United Kingdom"
        assert rows[0].sector == "Unknown"
        assert rows[0].currency == "EUR"
        assert rows[0].weight_pct == 0.005

        assert rows[1].ticker == "FIBERCOP SPA"
        assert rows[1].country == "Italy"
