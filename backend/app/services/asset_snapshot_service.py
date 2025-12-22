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
) -> list[SnapshotSummary]:
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

    # If no results, return empty list
    if not results:
        return []

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
        )
        summaries.append(summary)

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

    return summaries
