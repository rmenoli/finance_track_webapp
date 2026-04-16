import csv
import tempfile
from pathlib import Path

from process_holding_csv.base import (
    COUNTRY_MAP,
    SECTOR_MAP,
    HoldingRow,
    standardize_country,
    standardize_sector,
    write_csv,
)


class TestStandardizeCountry:
    def test_italian_name(self) -> None:
        assert standardize_country("Francia") == "France"

    def test_iso2_code(self) -> None:
        assert standardize_country("US") == "United States"

    def test_case_variant(self) -> None:
        assert standardize_country("Regno unito") == "United Kingdom"

    def test_unknown_passthrough(self) -> None:
        assert standardize_country("Atlantis") == "Atlantis"

    def test_dash(self) -> None:
        assert standardize_country("-") == "Unknown"


class TestStandardizeSector:
    def test_italian_sector(self) -> None:
        assert standardize_sector("Energia") == "Energy"

    def test_english_passthrough(self) -> None:
        assert standardize_sector("Technology") == "Technology"

    def test_unknown_passthrough(self) -> None:
        assert standardize_sector("NewSector") == "NewSector"

    def test_sconosciuta(self) -> None:
        assert standardize_sector("sconosciuta") == "Unknown"


class TestWriteCsv:
    def test_writes_correct_csv(self) -> None:
        rows = [
            HoldingRow(
                ticker="AAPL",
                country="United States",
                sector="Technology",
                currency="USD",
                weight_pct=0.038318,
            ),
            HoldingRow(
                ticker="NESN",
                country="Switzerland",
                sector="Consumer Staples",
                currency="CHF",
                weight_pct=0.005,
            ),
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)
        write_csv(rows, output_path)
        with open(output_path) as f:
            reader = csv.DictReader(f)
            result = list(reader)
        assert len(result) == 2
        assert result[0]["ticker"] == "AAPL"
        assert result[0]["country"] == "United States"
        assert result[0]["sector"] == "Technology"
        assert result[0]["currency"] == "USD"
        assert float(result[0]["weight_pct"]) == 0.038318
        output_path.unlink()
