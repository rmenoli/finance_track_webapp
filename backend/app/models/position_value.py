"""Position value model for storing current portfolio values."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PositionValue(Base):
    """Position value model for storing current portfolio values.

    Stores the most recent manually entered value for each ISIN.
    One row per ISIN with UPSERT semantics.
    """

    __tablename__ = "position_values"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ISIN - unique identifier
    isin: Mapped[str] = mapped_column(String(12), nullable=False, unique=True, index=True)

    # Current total value (manually entered by user)
    current_value: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint('isin', name='uq_position_value_isin'),
        Index('idx_position_value_isin', 'isin'),
    )

    def __repr__(self) -> str:
        """String representation of PositionValue."""
        return (
            f"<PositionValue(id={self.id}, isin={self.isin}, "
            f"current_value={self.current_value}, updated_at={self.updated_at})>"
        )
