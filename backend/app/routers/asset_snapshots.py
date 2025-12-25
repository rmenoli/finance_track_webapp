"""Asset snapshots API router."""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Path, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import CSVImportError
from app.schemas.asset_snapshot import (
    AssetSnapshotListResponse,
    AssetSnapshotResponse,
    SnapshotCreateResponse,
    SnapshotCSVImportResponse,
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


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    summary="Delete all snapshots",
    description="Delete all asset snapshots. WARNING: This operation cannot be undone!",
)
def delete_all_snapshots(db: Session = Depends(get_db)) -> dict:
    """Delete all snapshots."""
    deleted_count = asset_snapshot_service.delete_all_snapshots(db)
    return {
        "message": f"Successfully deleted {deleted_count} snapshot(s)",
        "deleted_count": deleted_count,
    }


@router.post(
    "/import-csv",
    response_model=SnapshotCSVImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Import snapshots from CSV",
    description="Import multiple asset snapshots from a CSV file. "
    "Returns detailed results for successful and failed imports.",
)
async def import_snapshots_csv_endpoint(
    file: UploadFile = File(..., description="Snapshot CSV file"),
    db: Session = Depends(get_db),
) -> SnapshotCSVImportResponse:
    """
    Import asset snapshots from CSV file.

    Expected CSV format:
    - Required columns: snapshot_date, asset_type, currency, value, exchange_rate, value_eur
    - Optional columns: asset_detail, created_at
    - Datetime format: ISO 8601 (e.g., 2023-01-17T00:00:00.397717)
    - Decimal format: Standard notation (e.g., 41800.00)

    Returns:
    - Summary of import (total, successful, failed)
    - List of successful imports with snapshot IDs
    - List of failed imports with detailed error messages
    """
    # Validate file type
    if not file.filename or not file.filename.endswith(".csv"):
        raise CSVImportError("File must be a CSV file")

    # Read file content
    try:
        content = await file.read()
        csv_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise CSVImportError("File must be UTF-8 encoded")
    except Exception as e:
        raise CSVImportError(f"Failed to read file: {str(e)}")

    # Import snapshots
    results = asset_snapshot_service.import_snapshots_from_csv(
        db=db,
        csv_content=csv_content,
    )

    # Convert to response schema
    return SnapshotCSVImportResponse(**results)
