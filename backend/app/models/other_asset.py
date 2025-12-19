"""Other asset model for storing non-ETF holdings."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OtherAsset(Base):
    """Other asset model for storing non-ETF holdings.

    Stores values for various asset types including crypto, cash in different
    accounts/currencies, CD accounts, and pension funds. The investments row
    is computed from portfolio summary and not stored in the database.

    UNIQUE constraint on (asset_type, asset_detail) ensures only one value
    per asset type and account combination.
    """

    __tablename__ = "other_assets"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Asset type (e.g., 'crypto', 'cash_eur', 'cash_czk', 'cd_account', 'pension_fund')
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Asset detail (account name for cash assets, NULL for others)
    asset_detail: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Currency (EUR or CZK)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Value in the specified currency
    value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint('asset_type', 'asset_detail', name='uq_other_asset_type_detail'),
        Index('idx_other_asset_type', 'asset_type'),
    )

    def __repr__(self) -> str:
        """String representation of OtherAsset."""
        return (
            f"<OtherAsset(id={self.id}, asset_type={self.asset_type}, "
            f"asset_detail={self.asset_detail}, currency={self.currency}, "
            f"value={self.value}, updated_at={self.updated_at})>"
        )
