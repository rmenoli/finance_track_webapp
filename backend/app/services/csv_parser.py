"""CSV parsing utilities for DEGIRO import."""

import csv
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Optional

from app.constants import TransactionType
from app.logging_config import log_with_context

logger = logging.getLogger(__name__)


class DEGIRORowData:
    """Parsed DEGIRO CSV row data."""

    def __init__(
        self,
        row_number: int,
        date: datetime.date,
        isin: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal,
        transaction_type: TransactionType,
        raw_row: dict,
    ):
        self.row_number = row_number
        self.date = date
        self.isin = isin
        self.quantity = quantity
        self.price = price
        self.fee = fee
        self.transaction_type = transaction_type
        self.raw_row = raw_row


def parse_european_decimal(value: str) -> Decimal:
    """
    Parse European number format (comma as decimal separator).

    Examples:
        "143,9000" -> Decimal("143.9000")
        "-3021,90" -> Decimal("-3021.90")
        "" -> Decimal("0.00")

    Args:
        value: String with European number format

    Returns:
        Decimal value

    Raises:
        ValueError: If value cannot be parsed
    """
    if not value or value.strip() == "":
        return Decimal("0.00")

    try:
        # Remove any whitespace and replace comma with dot
        clean_value = value.strip().replace(",", ".")
        return Decimal(clean_value)
    except InvalidOperation:
        raise ValueError(f"Cannot parse decimal value: {value}")


def parse_degiro_date(date_str: str) -> datetime.date:
    """
    Parse DEGIRO date format (DD-MM-YYYY).

    Args:
        date_str: Date string in DD-MM-YYYY format

    Returns:
        date object

    Raises:
        ValueError: If date cannot be parsed
    """
    try:
        return datetime.strptime(date_str.strip(), "%d-%m-%Y").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str} (expected DD-MM-YYYY)")


def parse_degiro_row(row: dict, row_number: int) -> DEGIRORowData:
    """
    Parse a single DEGIRO CSV row.

    Args:
        row: Dictionary from csv.DictReader
        row_number: Row number for error reporting (1-indexed)

    Returns:
        DEGIRORowData object

    Raises:
        ValueError: If row cannot be parsed
    """
    try:
        # Column 0: Date
        date = parse_degiro_date(row["Date"])

        # Column 3: ISIN
        isin = row["ISIN"].strip().upper()
        if not isin or len(isin) != 12:
            raise ValueError(f"Invalid ISIN: {isin}")

        # Column 6: Quantity (positive = BUY, negative = SELL)
        quantity_raw = parse_european_decimal(row["Quantity"])
        if quantity_raw > 0:
            transaction_type = TransactionType.BUY
            quantity = quantity_raw
        elif quantity_raw < 0:
            transaction_type = TransactionType.SELL
            quantity = abs(quantity_raw)
        else:
            raise ValueError("Quantity cannot be zero")

        # Column 7: Price
        price = parse_european_decimal(row["Price"])
        if price <= 0:
            raise ValueError(f"Price must be positive: {price}")

        # Column 14: Transaction and/or third party fees EUR
        fee_raw = parse_european_decimal(
            row.get("Transaction and/or third party fees EUR", "0")
        )
        fee = abs(fee_raw)  # Convert negative to positive

        return DEGIRORowData(
            row_number=row_number,
            date=date,
            isin=isin,
            quantity=quantity,
            price=price,
            fee=fee,
            transaction_type=transaction_type,
            raw_row=row,
        )

    except Exception as e:
        # Re-raise with row context
        raise ValueError(f"Row {row_number}: {str(e)}") from e


def parse_degiro_csv(csv_content: str) -> list[DEGIRORowData]:
    """
    Parse DEGIRO CSV content.

    Args:
        csv_content: CSV file content as string

    Returns:
        List of DEGIRORowData objects

    Raises:
        ValueError: If CSV format is invalid or required columns missing
    """
    try:
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file)

        # Validate required columns
        required_columns = {
            "Date",
            "Time",
            "ISIN",
            "Quantity",
            "Price",
            "Transaction and/or third party fees EUR",
        }

        if not reader.fieldnames:
            raise ValueError("CSV file is empty or has no header")

        missing_columns = required_columns - set(reader.fieldnames)
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {', '.join(missing_columns)}"
            )

        # Parse rows
        parsed_rows = []
        for idx, row in enumerate(reader, start=1):
            # Skip empty rows
            if not any(row.values()):
                continue

            try:
                parsed_data = parse_degiro_row(row, idx)
                parsed_rows.append(parsed_data)
            except ValueError:
                # Re-raise to be caught by import service
                raise

        return parsed_rows

    except csv.Error as e:
        raise ValueError(f"Invalid CSV format: {str(e)}") from e
