"""CSV parsing utilities for snapshot import."""

import csv
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Optional

from app.logging_config import log_with_context

logger = logging.getLogger(__name__)


class SnapshotRowData:
    """Parsed snapshot CSV row data."""

    def __init__(
        self,
        row_number: int,
        snapshot_date: datetime,
        asset_type: str,
        asset_detail: Optional[str],
        currency: str,
        value: Decimal,
        exchange_rate: Decimal,
        value_eur: Decimal,
        created_at: Optional[datetime],
        raw_row: dict,
    ):
        self.row_number = row_number
        self.snapshot_date = snapshot_date
        self.asset_type = asset_type
        self.asset_detail = asset_detail
        self.currency = currency
        self.value = value
        self.exchange_rate = exchange_rate
        self.value_eur = value_eur
        self.created_at = created_at
        self.raw_row = raw_row


def parse_decimal(value: str) -> Decimal:
    """
    Parse decimal value.

    Args:
        value: String with decimal number

    Returns:
        Decimal value

    Raises:
        ValueError: If value cannot be parsed
    """
    if not value or value.strip() == "":
        return Decimal("0.00")

    try:
        clean_value = value.strip()
        return Decimal(clean_value)
    except InvalidOperation:
        raise ValueError(f"Cannot parse decimal value: {value}")


def parse_iso_datetime(datetime_str: str) -> datetime:
    """
    Parse ISO 8601 datetime format.

    Args:
        datetime_str: Datetime string in ISO 8601 format

    Returns:
        datetime object

    Raises:
        ValueError: If datetime cannot be parsed
    """
    try:
        # Try parsing with fromisoformat (Python 3.7+)
        return datetime.fromisoformat(datetime_str.strip())
    except ValueError:
        # Try parsing with strptime as fallback
        try:
            return datetime.strptime(datetime_str.strip(), "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            raise ValueError(
                f"Invalid datetime format: {datetime_str} (expected ISO 8601 format)"
            )


def parse_snapshot_row(row: dict, row_number: int) -> SnapshotRowData:
    """
    Parse a single snapshot CSV row.

    Args:
        row: Dictionary from csv.DictReader
        row_number: Row number for error reporting (1-indexed)

    Returns:
        SnapshotRowData object

    Raises:
        ValueError: If row cannot be parsed
    """
    try:
        # snapshot_date (required)
        snapshot_date = parse_iso_datetime(row["snapshot_date"])

        # asset_type (required)
        asset_type = row["asset_type"].strip()
        if not asset_type or len(asset_type) > 50:
            raise ValueError(
                f"Invalid asset_type: must be between 1 and 50 characters"
            )

        # asset_detail (optional)
        asset_detail_raw = row.get("asset_detail", "").strip()
        asset_detail = asset_detail_raw if asset_detail_raw else None
        if asset_detail and len(asset_detail) > 100:
            raise ValueError("asset_detail cannot exceed 100 characters")

        # currency (required)
        currency = row["currency"].strip().upper()
        if len(currency) != 3:
            raise ValueError(f"Invalid currency: must be exactly 3 characters")

        # value (required)
        value = parse_decimal(row["value"])
        if value < 0:
            raise ValueError("value cannot be negative")

        # exchange_rate (required)
        exchange_rate = parse_decimal(row["exchange_rate"])
        if exchange_rate <= 0:
            raise ValueError("exchange_rate must be positive")

        # value_eur (required)
        value_eur = parse_decimal(row["value_eur"])
        if value_eur < 0:
            raise ValueError("value_eur cannot be negative")

        # created_at (optional, defaults to None)
        created_at = None
        created_at_raw = row.get("created_at", "").strip()
        if created_at_raw:
            created_at = parse_iso_datetime(created_at_raw)

        return SnapshotRowData(
            row_number=row_number,
            snapshot_date=snapshot_date,
            asset_type=asset_type,
            asset_detail=asset_detail,
            currency=currency,
            value=value,
            exchange_rate=exchange_rate,
            value_eur=value_eur,
            created_at=created_at,
            raw_row=row,
        )

    except Exception as e:
        # Re-raise with row context
        raise ValueError(f"Row {row_number}: {str(e)}") from e


def parse_snapshot_csv(csv_content: str) -> list[SnapshotRowData]:
    """
    Parse snapshot CSV content.

    Args:
        csv_content: CSV file content as string

    Returns:
        List of SnapshotRowData objects

    Raises:
        ValueError: If CSV format is invalid or required columns missing
    """
    try:
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file)

        # Validate required columns
        required_columns = {
            "snapshot_date",
            "asset_type",
            "currency",
            "value",
            "exchange_rate",
            "value_eur",
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
                parsed_data = parse_snapshot_row(row, idx)
                parsed_rows.append(parsed_data)
            except ValueError:
                # Re-raise to be caught by import service
                raise

        return parsed_rows

    except csv.Error as e:
        raise ValueError(f"Invalid CSV format: {str(e)}") from e
