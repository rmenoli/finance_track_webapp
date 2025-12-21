"""User setting model for storing user preferences."""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserSetting(Base):
    """User setting model for storing user preferences.

    Stores key-value pairs for user settings (e.g., exchange rates, preferences).
    One row per setting_key with UPSERT semantics.
    """

    __tablename__ = "user_settings"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Setting key - unique identifier
    setting_key: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    # Setting value (stored as string, converted as needed)
    setting_value: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint('setting_key', name='uq_user_setting_key'),
        Index('idx_user_setting_key', 'setting_key'),
    )

    def __repr__(self) -> str:
        """String representation of UserSetting."""
        return (
            f"<UserSetting(id={self.id}, setting_key={self.setting_key}, "
            f"setting_value={self.setting_value}, updated_at={self.updated_at})>"
        )
