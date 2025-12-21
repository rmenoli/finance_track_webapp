"""Asset snapshot model for storing historical asset values."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AssetSnapshot(Base):
    """Asset snapshot model for storing historical asset values.

    Stores point-in-time snapshots of all assets including:
    - Synthetic investments row (computed from portfolio)
    - Real assets from other_assets table
    - Cash accounts are stored separately (no aggregation)

    Each snapshot row represents one asset at a specific datetime.
    Multiple snapshots can exist for the same date (no uniqueness constraint).
    """

    __tablename__ = "asset_snapshots"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Snapshot metadata
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # Asset identification
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    asset_detail: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Financial data (stored, not computed)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    value_eur: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Audit timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Table constraints and indexes
    __table_args__ = (
        Index('idx_snapshot_date', 'snapshot_date'),
        Index('idx_snapshot_date_asset_type', 'snapshot_date', 'asset_type'),
    )

    def __repr__(self) -> str:
        """String representation of AssetSnapshot."""
        return (
            f"<AssetSnapshot(id={self.id}, snapshot_date={self.snapshot_date}, "
            f"asset_type={self.asset_type}, asset_detail={self.asset_detail}, "
            f"value={self.value}, value_eur={self.value_eur})>"
        )
