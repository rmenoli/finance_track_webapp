from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.constants import TransactionType
from app.database import Base


class Transaction(Base):
    """Transaction model for ETF portfolio tracking."""

    __tablename__ = "transactions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Transaction data
    date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    isin: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    broker: Mapped[str] = mapped_column(String(100), nullable=False)
    fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    price_per_unit: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    units: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType), nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("units > 0", name="check_positive_units"),
        CheckConstraint("price_per_unit > 0", name="check_positive_price"),
        CheckConstraint("fee >= 0", name="check_non_negative_fee"),
        # Composite index for date and ISIN queries
        Index("idx_date_isin", "date", "isin"),
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, date={self.date}, isin={self.isin}, "
            f"type={self.transaction_type}, units={self.units})>"
        )
