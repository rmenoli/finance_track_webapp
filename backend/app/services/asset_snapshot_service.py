"""Asset snapshot service for business logic."""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from sqlalchemy import func

from app.exceptions import SnapshotNotFoundError
from app.logging_config import log_with_context
from app.models.asset_snapshot import AssetSnapshot
from app.schemas.asset_snapshot import (
    AssetTypeBreakdown,
    CurrencyBreakdown,
    SnapshotMetadata,
    SnapshotSummary,
)
from app.services import other_asset_service

logger = logging.getLogger(__name__)


def create_snapshot(
    db: Session, snapshot_datetime: datetime | None = None
) -> tuple[list[AssetSnapshot], SnapshotMetadata]:
    """
    Create a snapshot of current asset state.

    Captures all assets from get_all_other_assets_with_investments() and stores
    each asset as a separate snapshot row (no aggregation). Includes synthetic
    investments row and all real assets with their account details.

    Args:
        db: Database session
        snapshot_datetime: Optional timestamp for snapshot (defaults to now)

    Returns:
        Tuple of (list of created snapshots, snapshot metadata)
    """
    # Get all assets including synthetic investments row
    assets, exchange_rate = other_asset_service.get_all_other_assets_with_investments(db)

    snapshot_date = snapshot_datetime or datetime.utcnow()
    snapshots = []
    total_value_eur = Decimal("0")

    # Store each asset as-is (no aggregation)
    for asset in assets:
        # Calculate value_eur based on currency
        if asset.currency == "CZK":
            value_eur = asset.value / exchange_rate
        else:
            value_eur = asset.value

        # Create snapshot row
        snapshot = AssetSnapshot(
            snapshot_date=snapshot_date,
            asset_type=asset.asset_type,
            asset_detail=asset.asset_detail,  # Includes account name or NULL
            currency=asset.currency,
            value=asset.value,
            exchange_rate=exchange_rate,
            value_eur=value_eur,
        )
        snapshots.append(snapshot)
        total_value_eur += value_eur

    # Bulk insert
    db.add_all(snapshots)
    db.commit()

    # Refresh all snapshots to get database-generated IDs
    for snapshot in snapshots:
        db.refresh(snapshot)

    # Create metadata
    metadata = SnapshotMetadata(
        snapshot_date=snapshot_date,
        exchange_rate_used=exchange_rate,
        total_assets_captured=len(snapshots),
        total_value_eur=total_value_eur,
    )

    # AUDIT LOG
    log_with_context(
        logger,
        logging.INFO,
        "Asset snapshot created",
        operation="CREATE",
        snapshot_date=snapshot_date.isoformat(),
        total_assets=len(snapshots),
        total_value_eur=str(total_value_eur),
        exchange_rate=str(exchange_rate),
    )

    return snapshots, metadata


def get_snapshots(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    asset_type: str | None = None,
) -> list[AssetSnapshot]:
    """
    Get asset snapshots with optional filtering.

    Args:
        db: Database session
        start_date: Optional start date filter (inclusive)
        end_date: Optional end date filter (inclusive)
        asset_type: Optional asset type filter

    Returns:
        List of asset snapshots ordered by snapshot_date DESC, asset_type ASC
    """
    query = db.query(AssetSnapshot)

    if start_date:
        query = query.filter(AssetSnapshot.snapshot_date >= start_date)
    if end_date:
        query = query.filter(AssetSnapshot.snapshot_date <= end_date)
    if asset_type:
        query = query.filter(AssetSnapshot.asset_type == asset_type)

    return query.order_by(
        AssetSnapshot.snapshot_date.desc(), AssetSnapshot.asset_type.asc()
    ).all()


def get_snapshots_by_date(db: Session, snapshot_date: datetime) -> list[AssetSnapshot]:
    """
    Get all asset snapshots for a specific date.

    Args:
        db: Database session
        snapshot_date: Snapshot date to filter by

    Returns:
        List of asset snapshots for that date, ordered by asset_type

    Raises:
        SnapshotNotFoundError: If no snapshots exist for that date
    """
    snapshots = (
        db.query(AssetSnapshot)
        .filter(AssetSnapshot.snapshot_date == snapshot_date)
        .order_by(AssetSnapshot.asset_type.asc())
        .all()
    )

    if not snapshots:
        raise SnapshotNotFoundError(snapshot_date.isoformat())

    return snapshots


def delete_snapshots_by_date(db: Session, snapshot_date: datetime) -> int:
    """
    Delete all asset snapshots for a specific date.

    Args:
        db: Database session
        snapshot_date: Snapshot date to delete

    Returns:
        Number of snapshot rows deleted

    Raises:
        SnapshotNotFoundError: If no snapshots exist for that date
    """
    # Get snapshots to check existence and for audit log
    snapshots = (
        db.query(AssetSnapshot)
        .filter(AssetSnapshot.snapshot_date == snapshot_date)
        .all()
    )

    if not snapshots:
        raise SnapshotNotFoundError(snapshot_date.isoformat())

    # Store for audit log
    deleted_count = len(snapshots)

    # Delete all snapshots for this date
    db.query(AssetSnapshot).filter(
        AssetSnapshot.snapshot_date == snapshot_date
    ).delete()
    db.commit()

    # AUDIT LOG
    log_with_context(
        logger,
        logging.INFO,
        "Asset snapshots deleted",
        operation="DELETE",
        snapshot_date=snapshot_date.isoformat(),
        deleted_count=deleted_count,
    )

    return deleted_count


def get_snapshot_summaries(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> tuple[list[SnapshotSummary], Decimal]:
    """
    Get summary statistics for snapshots grouped by date.

    For each snapshot date, calculates:
    - Total portfolio value in EUR (sum of all value_eur)
    - Breakdown by currency (sum of value grouped by currency)
    - Breakdown by asset type (sum of value_eur grouped by asset_type)

    Args:
        db: Database session
        start_date: Optional start date filter (inclusive)
        end_date: Optional end date filter (inclusive)

    Returns:
        List of SnapshotSummary objects ordered by snapshot_date DESC
    """
    # Build query with date filters
    query = db.query(
        AssetSnapshot.snapshot_date,
        AssetSnapshot.currency,
        AssetSnapshot.asset_type,
        AssetSnapshot.exchange_rate,
        func.sum(AssetSnapshot.value).label("total_value"),
        func.sum(AssetSnapshot.value_eur).label("total_value_eur"),
    )

    if start_date:
        query = query.filter(AssetSnapshot.snapshot_date >= start_date)
    if end_date:
        query = query.filter(AssetSnapshot.snapshot_date <= end_date)

    # Group by snapshot_date, currency, asset_type, exchange_rate
    # Order by snapshot_date DESC
    results = (
        query.group_by(
            AssetSnapshot.snapshot_date,
            AssetSnapshot.currency,
            AssetSnapshot.asset_type,
            AssetSnapshot.exchange_rate,
        )
        .order_by(AssetSnapshot.snapshot_date.desc())
        .all()
    )

    # If no results, return empty list and 0 avg_monthly_increment
    if not results:
        return [], Decimal("0")

    # Group results by snapshot_date using Python
    summaries_dict: dict[datetime, dict] = {}

    for row in results:
        snapshot_date = row.snapshot_date
        currency = row.currency
        asset_type = row.asset_type
        exchange_rate = row.exchange_rate
        total_value = row.total_value
        total_value_eur = row.total_value_eur

        # Initialize summary for this date if not exists
        if snapshot_date not in summaries_dict:
            summaries_dict[snapshot_date] = {
                "snapshot_date": snapshot_date,
                "exchange_rate_used": exchange_rate,
                "total_value_eur": Decimal("0"),
                "by_currency": {},
                "by_asset_type": {},
            }

        # Accumulate total EUR value
        summaries_dict[snapshot_date]["total_value_eur"] += total_value_eur

        # Accumulate currency breakdown
        if currency in summaries_dict[snapshot_date]["by_currency"]:
            summaries_dict[snapshot_date]["by_currency"][currency] += total_value
        else:
            summaries_dict[snapshot_date]["by_currency"][currency] = total_value

        # Accumulate asset type breakdown
        if asset_type in summaries_dict[snapshot_date]["by_asset_type"]:
            summaries_dict[snapshot_date]["by_asset_type"][asset_type] += total_value_eur
        else:
            summaries_dict[snapshot_date]["by_asset_type"][asset_type] = total_value_eur

    # Convert to list of SnapshotSummary objects
    summaries = []
    for snapshot_date in sorted(summaries_dict.keys(), reverse=True):  # DESC order
        summary_data = summaries_dict[snapshot_date]

        # Convert currency dict to list of CurrencyBreakdown
        by_currency = [
            CurrencyBreakdown(currency=curr, total_value=val)
            for curr, val in sorted(summary_data["by_currency"].items())
        ]

        # Convert asset_type dict to list of AssetTypeBreakdown
        by_asset_type = [
            AssetTypeBreakdown(asset_type=asset_type, total_value_eur=val)
            for asset_type, val in sorted(summary_data["by_asset_type"].items())
        ]

        summary = SnapshotSummary(
            snapshot_date=snapshot_date,
            total_value_eur=summary_data["total_value_eur"],
            exchange_rate_used=summary_data["exchange_rate_used"],
            by_currency=by_currency,
            by_asset_type=by_asset_type,
            absolute_change_from_oldest=Decimal("0"),  # Placeholder, calculated below
            percentage_change_from_oldest=Decimal("0"),  # Placeholder, calculated below
        )
        summaries.append(summary)

    # Calculate absolute and percentage change from oldest snapshot (baseline)
    if summaries:
        # Oldest snapshot is last element (DESC order)
        oldest_value = summaries[-1].total_value_eur
        oldest_date = summaries[-1].snapshot_date

        # Latest snapshot is first element (DESC order)
        latest_value = summaries[0].total_value_eur
        latest_date = summaries[0].snapshot_date

        # Calculate days between oldest and latest
        days_between = (latest_date - oldest_date).days

        # Calculate average monthly increment
        # If 0 or 1 summaries, or days_between is 0, avg_monthly_increment = 0
        if len(summaries) <= 1 or days_between == 0:
            avg_monthly_increment = Decimal("0.00")
        else:
            # Formula: ((latest - oldest) / days) * 30
            value_change = latest_value - oldest_value
            avg_monthly_increment = ((value_change / Decimal(str(days_between))) * Decimal("30")).quantize(Decimal("0.01"))

        for summary in summaries:
            # Calculate absolute change: current - oldest
            absolute_change = summary.total_value_eur - oldest_value

            if oldest_value > 0:
                # Calculate percentage: ((current - oldest) / oldest) × 100
                percentage_change = (
                    absolute_change
                    / oldest_value
                    * Decimal("100")
                )
            else:
                # Avoid division by zero - set to 0%
                percentage_change = Decimal("0")

            # Update changes in summary
            summary.absolute_change_from_oldest = absolute_change
            summary.percentage_change_from_oldest = percentage_change
    else:
        # Empty summaries, set avg_monthly_increment to 0
        avg_monthly_increment = Decimal("0")

    # AUDIT LOG
    log_with_context(
        logger,
        logging.INFO,
        "Snapshot summaries retrieved",
        operation="READ",
        summary_count=len(summaries),
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None,
    )

    return summaries, avg_monthly_increment


def import_snapshots_from_csv(db: Session, csv_content: str) -> dict:
    """
    Import asset snapshots from CSV file.

    Args:
        db: Database session
        csv_content: CSV file content as string

    Returns:
        Dictionary with import results:
        {
            "total_rows": int,
            "successful": int,
            "failed": int,
            "results": [{"row": int, "snapshot_id": int, ...}],
            "errors": [{"row": int, "errors": [...], ...}]
        }

    Raises:
        ValueError: If CSV format is invalid or required columns missing
    """
    from app.services.snapshot_csv_parser import parse_snapshot_csv

    results = {
        "total_rows": 0,
        "successful": 0,
        "failed": 0,
        "results": [],
        "errors": [],
    }

    try:
        # Parse CSV
        parsed_rows = parse_snapshot_csv(csv_content)
        results["total_rows"] = len(parsed_rows)

        log_with_context(
            logger,
            logging.INFO,
            "Starting snapshot CSV import",
            total_rows=len(parsed_rows),
        )

    except ValueError as e:
        # File-level parsing error
        log_with_context(
            logger,
            logging.ERROR,
            "Snapshot CSV parsing failed",
            error=str(e),
        )
        raise

    # Process each row
    for row_data in parsed_rows:
        try:
            # Create AssetSnapshot record
            snapshot = AssetSnapshot(
                snapshot_date=row_data.snapshot_date,
                asset_type=row_data.asset_type,
                asset_detail=row_data.asset_detail,
                currency=row_data.currency,
                value=row_data.value,
                exchange_rate=row_data.exchange_rate,
                value_eur=row_data.value_eur,
                created_at=row_data.created_at or datetime.utcnow(),
            )

            db.add(snapshot)
            db.flush()  # Get the ID

            # Record success
            results["successful"] += 1
            results["results"].append({
                "row": row_data.row_number,
                "snapshot_id": snapshot.id,
                "snapshot_date": snapshot.snapshot_date,
                "asset_type": snapshot.asset_type,
            })

        except Exception as e:
            # Record failure
            results["failed"] += 1
            error_message = str(e)
            results["errors"].append({
                "row": row_data.row_number,
                "snapshot_date": row_data.snapshot_date.isoformat() if row_data.snapshot_date else None,
                "asset_type": row_data.asset_type,
                "errors": [error_message],
                "raw_data": row_data.raw_row,
            })

            log_with_context(
                logger,
                logging.WARNING,
                "Snapshot import failed for row",
                row=row_data.row_number,
                error=error_message,
            )

    # Commit if any successful
    if results["successful"] > 0:
        db.commit()
    else:
        db.rollback()

    # AUDIT LOG
    log_with_context(
        logger,
        logging.INFO,
        "Snapshot CSV import completed",
        operation="BULK_CREATE",
        total_rows=results["total_rows"],
        successful=results["successful"],
        failed=results["failed"],
        success_rate=f"{(results['successful'] / results['total_rows'] * 100):.2f}%" if results['total_rows'] > 0 else "0%",
    )

    return results


def delete_all_snapshots(db: Session) -> int:
    """
    Delete all asset snapshots from the database.

    WARNING: This is a destructive operation that cannot be undone.

    Args:
        db: Database session

    Returns:
        Number of snapshots deleted

    Raises:
        Exception: If database operation fails
    """
    try:
        # Get count before deletion
        count = db.query(AssetSnapshot).count()

        # Delete all snapshots
        db.query(AssetSnapshot).delete()
        db.commit()

        # AUDIT LOG
        log_with_context(
            logger,
            logging.WARNING,
            "All snapshots deleted",
            operation="BULK_DELETE",
            deleted_count=count,
        )

        return count

    except Exception as e:
        db.rollback()
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to delete all snapshots",
            operation="BULK_DELETE",
            error=str(e),
        )
        raise
