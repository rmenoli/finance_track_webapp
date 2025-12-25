"""Tests for CSV parsing utilities."""

import pytest
from datetime import date
from decimal import Decimal

from app.constants import TransactionType
from app.services.csv_parser import (
    parse_european_decimal,
    parse_degiro_date,
    parse_degiro_row,
    parse_degiro_csv,
)


class TestParseEuropeanDecimal:
    """Test European decimal parsing."""

    def test_parse_standard_decimal(self):
        """Test parsing standard European decimal."""
        assert parse_european_decimal("143,9000") == Decimal("143.9000")

    def test_parse_negative_decimal(self):
        """Test parsing negative European decimal."""
        assert parse_european_decimal("-3021,90") == Decimal("-3021.90")

    def test_parse_empty_string(self):
        """Test parsing empty string defaults to zero."""
        assert parse_european_decimal("") == Decimal("0.00")

    def test_parse_whitespace(self):
        """Test parsing whitespace string defaults to zero."""
        assert parse_european_decimal("   ") == Decimal("0.00")

    def test_parse_integer(self):
        """Test parsing integer without decimal."""
        assert parse_european_decimal("100") == Decimal("100")

    def test_parse_invalid_decimal(self):
        """Test parsing invalid decimal raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse decimal value"):
            parse_european_decimal("not-a-number")


class TestParseDegiroDate:
    """Test DEGIRO date parsing."""

    def test_parse_valid_date(self):
        """Test parsing valid DD-MM-YYYY date."""
        assert parse_degiro_date("11-12-2025") == date(2025, 12, 11)

    def test_parse_single_digit_day_month(self):
        """Test parsing with single digit day and month."""
        assert parse_degiro_date("05-03-2024") == date(2024, 3, 5)

    def test_parse_invalid_format(self):
        """Test parsing invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_degiro_date("2025-12-11")  # Wrong format

    def test_parse_invalid_date(self):
        """Test parsing invalid date raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_degiro_date("32-13-2025")  # Invalid day/month


class TestParseDegiroRow:
    """Test DEGIRO row parsing."""

    def test_parse_buy_transaction(self):
        """Test parsing BUY transaction (positive quantity)."""
        row = {
            "Date": "11-12-2025",
            "Time": "16:03",
            "ISIN": "IE00BK5BQT80",
            "Quantity": "21",
            "Price": "143,9000",
            "Transaction and/or third party fees EUR": "-3,00",
        }

        result = parse_degiro_row(row, 1)

        assert result.date == date(2025, 12, 11)
        assert result.isin == "IE00BK5BQT80"
        assert result.quantity == Decimal("21")
        assert result.price == Decimal("143.9000")
        assert result.fee == Decimal("3.00")  # Converted to positive
        assert result.transaction_type == TransactionType.BUY
        assert result.row_number == 1

    def test_parse_sell_transaction(self):
        """Test parsing SELL transaction (negative quantity)."""
        row = {
            "Date": "15-11-2025",
            "Time": "10:30",
            "ISIN": "US0378331005",
            "Quantity": "-10",
            "Price": "450,25",
            "Transaction and/or third party fees EUR": "-1,50",
        }

        result = parse_degiro_row(row, 2)

        assert result.quantity == Decimal("10")  # Converted to positive
        assert result.transaction_type == TransactionType.SELL
        assert result.fee == Decimal("1.50")

    def test_parse_empty_fee(self):
        """Test parsing with empty fee (defaults to zero)."""
        row = {
            "Date": "11-12-2025",
            "Time": "16:03",
            "ISIN": "IE00BK5BQT80",
            "Quantity": "21",
            "Price": "143,9000",
            "Transaction and/or third party fees EUR": "",
        }

        result = parse_degiro_row(row, 1)

        assert result.fee == Decimal("0.00")

    def test_parse_lowercase_isin(self):
        """Test ISIN is converted to uppercase."""
        row = {
            "Date": "11-12-2025",
            "Time": "16:03",
            "ISIN": "ie00bk5bqt80",  # Lowercase
            "Quantity": "21",
            "Price": "143,9000",
            "Transaction and/or third party fees EUR": "",
        }

        result = parse_degiro_row(row, 1)

        assert result.isin == "IE00BK5BQT80"  # Uppercase

    def test_parse_invalid_isin_length(self):
        """Test parsing with invalid ISIN length raises ValueError."""
        row = {
            "Date": "11-12-2025",
            "Time": "16:03",
            "ISIN": "TOOLONG123456",  # 14 characters
            "Quantity": "21",
            "Price": "143,9000",
            "Transaction and/or third party fees EUR": "",
        }

        with pytest.raises(ValueError, match="Row 1"):
            parse_degiro_row(row, 1)

    def test_parse_zero_quantity(self):
        """Test parsing with zero quantity raises ValueError."""
        row = {
            "Date": "11-12-2025",
            "Time": "16:03",
            "ISIN": "IE00BK5BQT80",
            "Quantity": "0",
            "Price": "143,9000",
            "Transaction and/or third party fees EUR": "",
        }

        with pytest.raises(ValueError, match="Quantity cannot be zero"):
            parse_degiro_row(row, 1)

    def test_parse_negative_price(self):
        """Test parsing with negative price raises ValueError."""
        row = {
            "Date": "11-12-2025",
            "Time": "16:03",
            "ISIN": "IE00BK5BQT80",
            "Quantity": "21",
            "Price": "-143,9000",
            "Transaction and/or third party fees EUR": "",
        }

        with pytest.raises(ValueError, match="Price must be positive"):
            parse_degiro_row(row, 1)


class TestParseDegiroCSV:
    """Test full CSV parsing."""

    def test_parse_valid_csv(self):
        """Test parsing valid DEGIRO CSV."""
        csv_content = """Date,Time,Product,ISIN,Reference exchange,Venue,Quantity,Price,,Local value,,Value EUR,Exchange rate,AutoFX Fee,Transaction and/or third party fees EUR,Total EUR,Order ID,
11-12-2025,16:03,VANGUARD FTSE ALL-WORLD...,IE00BK5BQT80,XET,XETA,21,"143,9000",EUR,"-3021,90",EUR,"-3021,90",,"0,00","-3,00","-3024,90",,b1d87359
15-11-2025,10:30,APPLE INC,US0378331005,NDQ,XNAS,-10,"450,25",USD,"4502,50",EUR,"4000,00","1,125","0,00","-1,50","3998,50",,c2e98460"""

        results = parse_degiro_csv(csv_content)

        assert len(results) == 2
        assert results[0].isin == "IE00BK5BQT80"
        assert results[0].transaction_type == TransactionType.BUY
        assert results[1].isin == "US0378331005"
        assert results[1].transaction_type == TransactionType.SELL

    def test_parse_empty_rows(self):
        """Test parsing CSV with empty rows (should skip)."""
        csv_content = """Date,Time,Product,ISIN,Reference exchange,Venue,Quantity,Price,,Local value,,Value EUR,Exchange rate,AutoFX Fee,Transaction and/or third party fees EUR,Total EUR,Order ID,
11-12-2025,16:03,VANGUARD FTSE ALL-WORLD...,IE00BK5BQT80,XET,XETA,21,"143,9000",EUR,"-3021,90",EUR,"-3021,90",,"0,00","-3,00","-3024,90",,b1d87359
,,,,,,,,,,,,,,,,
15-11-2025,10:30,APPLE INC,US0378331005,NDQ,XNAS,-10,"450,25",USD,"4502,50",EUR,"4000,00","1,125","0,00","-1,50","3998,50",,c2e98460"""

        results = parse_degiro_csv(csv_content)

        assert len(results) == 2  # Empty row skipped

    def test_parse_missing_columns(self):
        """Test parsing CSV with missing columns raises ValueError."""
        csv_content = """Date,Time,ISIN
11-12-2025,16:03,IE00BK5BQT80"""

        with pytest.raises(ValueError, match="Missing required columns"):
            parse_degiro_csv(csv_content)

    def test_parse_empty_csv(self):
        """Test parsing empty CSV raises ValueError."""
        csv_content = ""

        with pytest.raises(ValueError, match="CSV file is empty"):
            parse_degiro_csv(csv_content)

    def test_parse_header_only(self):
        """Test parsing CSV with only header (no data rows)."""
        csv_content = """Date,Time,Product,ISIN,Reference exchange,Venue,Quantity,Price,,Local value,,Value EUR,Exchange rate,AutoFX Fee,Transaction and/or third party fees EUR,Total EUR,Order ID,"""

        results = parse_degiro_csv(csv_content)

        assert len(results) == 0  # No data rows

    def test_parse_malformed_row(self):
        """Test parsing with malformed row raises ValueError."""
        csv_content = """Date,Time,Product,ISIN,Reference exchange,Venue,Quantity,Price,,Local value,,Value EUR,Exchange rate,AutoFX Fee,Transaction and/or third party fees EUR,Total EUR,Order ID,
11-12-2025,16:03,VANGUARD FTSE ALL-WORLD...,IE00BK5BQT80,XET,XETA,21,"143,9000",EUR,"-3021,90",EUR,"-3021,90",,"0,00","-3,00","-3024,90",,b1d87359
invalid-date,10:30,APPLE INC,US0378331005,NDQ,XNAS,-10,"450,25",USD,"4502,50",EUR,"4000,00","1,125","0,00","-1,50","3998,50",,c2e98460"""

        with pytest.raises(ValueError, match="Row 2"):
            parse_degiro_csv(csv_content)
