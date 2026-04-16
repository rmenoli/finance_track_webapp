# backend/tests/test_etf_breakdown_service.py

import csv
import tempfile
from pathlib import Path

from app.services import etf_breakdown_service


def _write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["ticker", "country", "sector", "currency", "weight_pct"]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class TestLoadBreakdowns:
    def test_loads_valid_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            _write_csv(
                data_dir / "IE00BK5BQT80.csv",
                [
                    {"ticker": "AAPL", "country": "United States", "sector": "Technology", "currency": "USD", "weight_pct": "0.04"},
                    {"ticker": "MSFT", "country": "United States", "sector": "Technology", "currency": "USD", "weight_pct": "0.03"},
                    {"ticker": "NESN", "country": "Switzerland", "sector": "Consumer Staples", "currency": "CHF", "weight_pct": "0.01"},
                ],
            )
            etf_breakdown_service.load_breakdowns(data_dir)

            result = etf_breakdown_service.get_breakdown("IE00BK5BQT80")
            assert result is not None
            assert result["by_country"][0]["name"] == "United States"
            assert abs(result["by_country"][0]["weight_pct"] - 0.07) < 1e-6
            assert result["by_country"][1]["name"] == "Switzerland"

    def test_aggregates_sectors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            _write_csv(
                data_dir / "IE00BK5BQT80.csv",
                [
                    {"ticker": "AAPL", "country": "US", "sector": "Technology", "currency": "USD", "weight_pct": "0.04"},
                    {"ticker": "NESN", "country": "CH", "sector": "Consumer Staples", "currency": "CHF", "weight_pct": "0.01"},
                    {"ticker": "GOOG", "country": "US", "sector": "Technology", "currency": "USD", "weight_pct": "0.02"},
                ],
            )
            etf_breakdown_service.load_breakdowns(data_dir)

            result = etf_breakdown_service.get_breakdown("IE00BK5BQT80")
            sectors = {e["name"]: e["weight_pct"] for e in result["by_sector"]}
            assert abs(sectors["Technology"] - 0.06) < 1e-6
            assert abs(sectors["Consumer Staples"] - 0.01) < 1e-6

    def test_sorted_by_weight_descending(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            _write_csv(
                data_dir / "IE00BK5BQT80.csv",
                [
                    {"ticker": "A", "country": "Small", "sector": "X", "currency": "USD", "weight_pct": "0.01"},
                    {"ticker": "B", "country": "Large", "sector": "Y", "currency": "EUR", "weight_pct": "0.05"},
                ],
            )
            etf_breakdown_service.load_breakdowns(data_dir)

            result = etf_breakdown_service.get_breakdown("IE00BK5BQT80")
            assert result["by_country"][0]["name"] == "Large"
            assert result["by_country"][1]["name"] == "Small"

    def test_unknown_isin_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            etf_breakdown_service.load_breakdowns(Path(tmpdir))
            assert etf_breakdown_service.get_breakdown("UNKNOWN") is None

    def test_ignores_non_isin_filenames(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            _write_csv(
                data_dir / "notes.csv",
                [{"ticker": "X", "country": "Y", "sector": "Z", "currency": "USD", "weight_pct": "0.1"}],
            )
            _write_csv(
                data_dir / "IE00BK5BQT80.csv",
                [{"ticker": "A", "country": "US", "sector": "Tech", "currency": "USD", "weight_pct": "0.05"}],
            )
            etf_breakdown_service.load_breakdowns(data_dir)

            assert etf_breakdown_service.get_breakdown("notes") is None
            assert etf_breakdown_service.get_breakdown("IE00BK5BQT80") is not None

    def test_get_available_isins(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            _write_csv(
                data_dir / "IE00BK5BQT80.csv",
                [{"ticker": "A", "country": "US", "sector": "Tech", "currency": "USD", "weight_pct": "0.05"}],
            )
            _write_csv(
                data_dir / "IE00BFNM3P36.csv",
                [{"ticker": "B", "country": "UK", "sector": "Fin", "currency": "GBP", "weight_pct": "0.03"}],
            )
            etf_breakdown_service.load_breakdowns(data_dir)

            isins = etf_breakdown_service.get_available_isins()
            assert set(isins) == {"IE00BK5BQT80", "IE00BFNM3P36"}
