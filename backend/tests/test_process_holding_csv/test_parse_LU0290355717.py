import tempfile
from pathlib import Path

import openpyxl

from process_holding_csv.parse_LU0290355717 import parse


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
    ws.append([1, "FRANCE (GOVT OF)", "FR0013286192", "Francia", "EUR", "-",
               "Titoli di Stato", "Aa3", "-", "Governo", 0.008])
    ws.append([2, "ITALY (REPUBLIC OF)", "IT0005438004", "Italia", "EUR", "-",
               "Obbligazioni", "Baa3", "-", "Governo", 0.005])
    wb.save(path)


class TestParseDwsGovt:
    def test_parses_sample_rows(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            path = Path(f.name)
        _create_test_xlsx(path)

        rows = parse(path)
        path.unlink()

        assert len(rows) == 2
        assert rows[0].ticker == "FRANCE (GOVT OF)"
        assert rows[0].country == "France"
        assert rows[0].sector == "Government"
        assert rows[0].currency == "EUR"
        assert rows[0].weight_pct == 0.008

        assert rows[1].country == "Italy"
