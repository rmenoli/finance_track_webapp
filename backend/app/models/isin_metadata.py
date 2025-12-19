"""ISIN metadata model for storing ETF/asset information."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.constants import ISINType
from app.database import Base


class ISINMetadata(Base):
    """ISIN metadata model for storing ETF/asset information.

    Stores name and type for each ISIN (stock, bond, real-asset).
    One row per ISIN with UNIQUE constraint.
    """

    __tablename__ = "isin_metadata"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ISIN - unique identifier
    isin: Mapped[str] = mapped_column(String(12), nullable=False, unique=True, index=True)

    # Asset name (ETF name, stock name, etc.)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Asset type (stock, bond, real-asset)
    type: Mapped[ISINType] = mapped_column(Enum(ISINType), nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint('isin', name='uq_isin_metadata_isin'),
        Index('idx_isin_metadata_isin', 'isin'),
        Index('idx_isin_metadata_type', 'type'),
    )

    def __repr__(self) -> str:
        """String representation of ISINMetadata."""
        return (
            f"<ISINMetadata(id={self.id}, isin={self.isin}, "
            f"name={self.name}, type={self.type})>"
        )
