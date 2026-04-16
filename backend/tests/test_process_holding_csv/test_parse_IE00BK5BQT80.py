import tempfile
from pathlib import Path

import openpyxl

from process_holding_csv.parse_IE00BK5BQT80 import parse


def _create_test_xlsx(path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Dati delle partecipazioni"
    ws.append(["Questo file è stato scaricato il 13 apr 2026"] + [None] * 6)
    ws.append([None] * 7)
    ws.append(["Dati delle partecipazioni"] + [None] * 6)
    ws.append(["Vanguard FTSE All-World"] + [None] * 6)
    ws.append(["Al 28 feb 2026"] + [None] * 6)
    ws.append([None] * 7)
    ws.append(["Ticker", "Nome delle partecipazioni",
               "% del valore di mercato", "Settore", "Regione",
               "Valore di mercato", "Azioni"])
    ws.append(["NVDA", "NVIDIA Corp", "4,1278%", "Technology", "US",
               "2.483.217.028,89\xa0USD", "14.014.431"])
    ws.append(["2330", "Taiwan Semiconductor", "1,5433%", "Technology", "TW",
               "928.434.686,49\xa0USD", "14.525.000"])
    wb.save(path)


class TestParseVanguard:
    def test_parses_sample_rows(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            path = Path(f.name)
        _create_test_xlsx(path)

        rows = parse(path)
        path.unlink()

        assert len(rows) == 2
        assert rows[0].ticker == "NVDA"
        assert rows[0].country == "United States"
        assert rows[0].sector == "Technology"
        assert rows[0].currency == "USD"
        assert abs(rows[0].weight_pct - 0.041278) < 1e-6

        assert rows[1].ticker == "2330"
        assert rows[1].country == "Taiwan"
        assert rows[1].currency == "TWD"
