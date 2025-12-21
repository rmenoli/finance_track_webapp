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
