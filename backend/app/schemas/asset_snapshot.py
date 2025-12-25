"""Asset snapshot schemas for validation and serialization."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AssetSnapshotResponse(BaseModel):
    """Schema for asset snapshot responses."""

    id: int = Field(..., description="Snapshot ID")
    snapshot_date: datetime = Field(..., description="When snapshot was taken")
    asset_type: str = Field(..., description="Asset type (investments, crypto, cash_eur, etc.)")
    asset_detail: Optional[str] = Field(None, description="Account name for cash assets, NULL for others")
    currency: str = Field(..., description="Currency (EUR or CZK)")
    value: Decimal = Field(..., description="Value in native currency")
    exchange_rate: Decimal = Field(..., description="Exchange rate (CZK per 1 EUR) at snapshot time")
    value_eur: Decimal = Field(..., description="Value converted to EUR using snapshot exchange rate")
    created_at: datetime = Field(..., description="When record was created")

    model_config = ConfigDict(from_attributes=True)


class SnapshotMetadata(BaseModel):
    """Metadata about a snapshot creation."""

    snapshot_date: datetime = Field(..., description="Snapshot timestamp")
    exchange_rate_used: Decimal = Field(..., description="Exchange rate used for conversion")
    total_assets_captured: int = Field(..., description="Number of asset rows captured")
    total_value_eur: Decimal = Field(..., description="Total portfolio value in EUR")


class AssetSnapshotListResponse(BaseModel):
    """Schema for list of asset snapshots with metadata."""

    snapshots: list[AssetSnapshotResponse]
    total: int = Field(..., description="Total number of snapshot rows returned")
    metadata: Optional[SnapshotMetadata] = Field(None, description="Snapshot metadata (if grouped by date)")

    model_config = ConfigDict(from_attributes=True)


class SnapshotCreateResponse(BaseModel):
    """Schema for snapshot creation response."""

    message: str = Field(..., description="Success message")
    metadata: SnapshotMetadata
    snapshots: list[AssetSnapshotResponse]

    model_config = ConfigDict(from_attributes=True)


class CurrencyBreakdown(BaseModel):
    """Schema for currency breakdown in snapshot summary."""

    currency: str = Field(..., description="Currency code (EUR or CZK)")
    total_value: Decimal = Field(..., description="Sum of values in native currency")


class AssetTypeBreakdown(BaseModel):
    """Schema for asset type breakdown in snapshot summary."""

    asset_type: str = Field(..., description="Asset type identifier")
    total_value_eur: Decimal = Field(..., description="Sum of EUR-converted values")


class SnapshotSummary(BaseModel):
    """Schema for snapshot summary statistics for a single date."""

    snapshot_date: datetime = Field(..., description="The snapshot date")
    total_value_eur: Decimal = Field(..., description="Total portfolio value in EUR")
    exchange_rate_used: Decimal = Field(..., description="Exchange rate for that snapshot")
    by_currency: list[CurrencyBreakdown] = Field(..., description="Currency breakdown")
    by_asset_type: list[AssetTypeBreakdown] = Field(..., description="Asset type breakdown")
    absolute_change_from_oldest: Decimal = Field(
        ...,
        description="Absolute value change from oldest snapshot in filtered result set in EUR (0 for oldest snapshot)"
    )
    percentage_change_from_oldest: Decimal = Field(
        ...,
        description="Percentage change from oldest snapshot in filtered result set (0 for oldest snapshot)"
    )


class SnapshotSummaryListResponse(BaseModel):
    """Schema for list of snapshot summaries."""

    summaries: list[SnapshotSummary] = Field(..., description="List of summaries per date")
    total: int = Field(..., description="Number of snapshot dates returned")
    avg_monthly_increment: Decimal = Field(
        ...,
        description="Average monthly portfolio increment in EUR (calculated as total change divided by days, normalized to 30 days). Returns 0 if 0 or 1 snapshots."
    )


# CSV Import Schemas
class SnapshotCSVImportResult(BaseModel):
    """Schema for a single successful snapshot import."""

    row: int = Field(..., description="Row number (1-indexed, excluding header)")
    snapshot_id: int = Field(..., description="Created snapshot ID")
    snapshot_date: datetime = Field(..., description="Snapshot datetime")
    asset_type: str = Field(..., description="Asset type")


class SnapshotCSVImportError(BaseModel):
    """Schema for a single failed snapshot import."""

    row: int = Field(..., description="Row number (1-indexed, excluding header)")
    snapshot_date: Optional[str] = Field(
        None, description="Snapshot date from failed row (if parseable)"
    )
    asset_type: Optional[str] = Field(
        None, description="Asset type from failed row (if parseable)"
    )
    errors: list[str] = Field(..., description="List of validation error messages")
    raw_data: Optional[dict] = Field(
        None, description="Raw CSV row data for debugging"
    )


class SnapshotCSVImportResponse(BaseModel):
    """Schema for snapshot CSV import response."""

    from pydantic import computed_field

    total_rows: int = Field(..., description="Total rows processed (excluding header)")
    successful: int = Field(..., description="Number of successfully imported snapshots")
    failed: int = Field(..., description="Number of failed rows")
    results: list[SnapshotCSVImportResult] = Field(
        default_factory=list, description="Successful imports"
    )
    errors: list[SnapshotCSVImportError] = Field(
        default_factory=list, description="Failed imports with details"
    )

    @computed_field
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_rows == 0:
            return 0.0
        return round((self.successful / self.total_rows) * 100, 2)
