"""API integration tests for ETF breakdown endpoints."""

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


class TestETFBreakdownAPI:
    def test_get_breakdown_success(self, client) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            _write_csv(
                data_dir / "IE00BK5BQT80.csv",
                [
                    {"ticker": "AAPL", "country": "United States", "sector": "Technology", "currency": "USD", "weight_pct": "0.04"},
                    {"ticker": "NESN", "country": "Switzerland", "sector": "Consumer Staples", "currency": "CHF", "weight_pct": "0.01"},
                ],
            )
            etf_breakdown_service.load_breakdowns(data_dir)

            response = client.get("/v1/etf-breakdown/IE00BK5BQT80")
            assert response.status_code == 200
            data = response.json()
            assert data["isin"] == "IE00BK5BQT80"
            assert len(data["by_country"]) == 2
            assert data["by_country"][0]["name"] == "United States"
            assert len(data["by_sector"]) == 2
            assert len(data["by_currency"]) == 2

    def test_get_breakdown_not_found(self, client) -> None:
        etf_breakdown_service._cache.clear()
        response = client.get("/v1/etf-breakdown/UNKNOWN12345")
        assert response.status_code == 404

    def test_list_available_isins(self, client) -> None:
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

            response = client.get("/v1/etf-breakdown/")
            assert response.status_code == 200
            data = response.json()
            assert set(data["isins"]) == {"IE00BK5BQT80", "IE00BFNM3P36"}
