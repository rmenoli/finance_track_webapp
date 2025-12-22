"""Asset snapshots API router."""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.asset_snapshot import (
    AssetSnapshotListResponse,
    AssetSnapshotResponse,
    SnapshotCreateResponse,
    SnapshotSummaryListResponse,
)
from app.services import asset_snapshot_service

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.post(
    "",
    response_model=SnapshotCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create asset snapshot",
    description="Capture current state of all assets (investments + other assets) as a snapshot. Each asset is stored separately with no aggregation.",
)
def create_snapshot(
    snapshot_datetime: datetime | None = Query(
        None, description="Optional timestamp for snapshot (defaults to now)"
    ),
    db: Session = Depends(get_db),
) -> SnapshotCreateResponse:
    """Create a snapshot of current asset state."""
    snapshots, metadata = asset_snapshot_service.create_snapshot(db, snapshot_datetime)

    return SnapshotCreateResponse(
        message="Snapshot created successfully",
        metadata=metadata,
        snapshots=[AssetSnapshotResponse.model_validate(s) for s in snapshots],
    )


@router.get(
    "",
    response_model=AssetSnapshotListResponse,
    summary="List asset snapshots",
    description="Get asset snapshots with optional date range and asset type filtering",
)
def list_snapshots(
    start_date: datetime | None = Query(
        None, description="Filter snapshots from this date (inclusive)"
    ),
    end_date: datetime | None = Query(
        None, description="Filter snapshots until this date (inclusive)"
    ),
    asset_type: str | None = Query(None, description="Filter by asset type"),
    db: Session = Depends(get_db),
) -> AssetSnapshotListResponse:
    """List asset snapshots with optional filters."""
    snapshots = asset_snapshot_service.get_snapshots(
        db, start_date, end_date, asset_type
    )

    return AssetSnapshotListResponse(
        snapshots=[AssetSnapshotResponse.model_validate(s) for s in snapshots],
        total=len(snapshots),
        metadata=None,
    )


@router.get(
    "/summary",
    response_model=SnapshotSummaryListResponse,
    summary="Get snapshot summary statistics",
    description="Get aggregated summary statistics for snapshots. For each snapshot date, returns total portfolio value, breakdowns by currency and asset type.",
)
def get_snapshot_summary(
    start_date: datetime | None = Query(
        None, description="Filter summaries from this date (inclusive)"
    ),
    end_date: datetime | None = Query(
        None, description="Filter summaries until this date (inclusive)"
    ),
    db: Session = Depends(get_db),
) -> SnapshotSummaryListResponse:
    """
    Get summary statistics for snapshots.

    For each snapshot date, returns:
    - Total portfolio value in EUR
    - Breakdown by currency
    - Breakdown by asset type
    """
    summaries, avg_monthly_increment = asset_snapshot_service.get_snapshot_summaries(db, start_date, end_date)

    return SnapshotSummaryListResponse(
        summaries=summaries,
        total=len(summaries),
        avg_monthly_increment=avg_monthly_increment
    )


@router.delete(
    "/{snapshot_date}",
    status_code=status.HTTP_200_OK,
    summary="Delete snapshots by date",
    description="Delete all asset snapshots for a specific date",
)
def delete_snapshot_by_date(
    snapshot_date: datetime = Path(..., description="Snapshot date to delete"),
    db: Session = Depends(get_db),
) -> dict:
    """Delete all snapshots for a specific date."""
    deleted_count = asset_snapshot_service.delete_snapshots_by_date(db, snapshot_date)

    return {
        "message": f"Successfully deleted {deleted_count} snapshot(s) for {snapshot_date.isoformat()}",
        "deleted_count": deleted_count,
        "snapshot_date": snapshot_date.isoformat(),
    }
