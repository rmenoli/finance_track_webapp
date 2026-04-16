import tempfile
from pathlib import Path

from process_holding_csv.parse_IE00BFNM3P36 import parse


class TestParseIShaares:
    def test_parses_sample_rows(self) -> None:
        content = (
            'Al,"10/04/2026"\n'
            " \n"
            'Ticker dell\'emittente,Nome,Settore,Asset Class,Valore di mercato,'
            'Ponderazione (%),Valore nozionale,Nominale,Prezzo,Area Geografica,'
            'Cambio,Valuta di mercato\n'
            '"SNDK","SANDISK CORP","IT","Azionario","91.739.036,08","1,17",'
            '"91.739.036,08","107.704,00","851,77","Stati Uniti","NASDAQ","USD"\n'
            '"5801","FURUKAWA ELECTRIC LTD","Industriali","Azionario",'
            '"15.111.236,80","0,19","15.111.236,80","52.500,00","287,83",'
            '"Giappone","Tokyo Stock Exchange","JPY"\n'
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8-sig"
        ) as f:
            f.write(content)
            path = Path(f.name)

        rows = parse(path)
        path.unlink()

        assert len(rows) == 2

        assert rows[0].ticker == "SNDK"
        assert rows[0].country == "United States"
        assert rows[0].sector == "Technology"
        assert rows[0].currency == "USD"
        assert abs(rows[0].weight_pct - 0.0117) < 1e-6

        assert rows[1].ticker == "5801"
        assert rows[1].country == "Japan"
        assert rows[1].sector == "Industrials"
        assert rows[1].currency == "JPY"

    def test_parses_thousands_separator(self) -> None:
        content = (
            'Al,"10/04/2026"\n'
            " \n"
            'Ticker dell\'emittente,Nome,Settore,Asset Class,Valore di mercato,'
            'Ponderazione (%),Valore nozionale,Nominale,Prezzo,Area Geografica,'
            'Cambio,Valuta di mercato\n'
            '"TEST","TEST CORP","Energia","Azionario","1.000,00","12,34",'
            '"1.000,00","100,00","10,00","Francia","Euronext","EUR"\n'
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8-sig"
        ) as f:
            f.write(content)
            path = Path(f.name)

        rows = parse(path)
        path.unlink()

        assert len(rows) == 1
        assert abs(rows[0].weight_pct - 0.1234) < 1e-6
