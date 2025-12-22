"""User setting service for business logic."""

import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.logging_config import log_with_context
from app.models.user_setting import UserSetting

logger = logging.getLogger(__name__)

# Setting key constants
EXCHANGE_RATE_KEY = "czk_eur_exchange_rate"


def get_exchange_rate_setting(db: Session) -> Optional[UserSetting]:
    """
    Get the stored exchange rate setting object.

    Args:
        db: Database session

    Returns:
        UserSetting object if exists, None otherwise.
        To get the Decimal value: Decimal(result.setting_value)
    """
    return db.query(UserSetting).filter(
        UserSetting.setting_key == EXCHANGE_RATE_KEY
    ).first()


def update_exchange_rate_setting(db: Session, exchange_rate: Decimal) -> UserSetting:
    """
    Create or update the exchange rate setting (UPSERT operation).

    If setting exists, updates the value and updated_at.
    If setting doesn't exist, creates new record.

    Args:
        db: Database session
        exchange_rate: Exchange rate (CZK per 1 EUR)

    Returns:
        Created or updated user setting
    """
    # Check if setting exists
    existing = db.query(UserSetting).filter(
        UserSetting.setting_key == EXCHANGE_RATE_KEY
    ).first()

    if existing:
        # Update existing record
        old_value = existing.setting_value
        existing.setting_value = str(exchange_rate)
        # updated_at will auto-update via onupdate in model
        db.commit()
        db.refresh(existing)

        # AUDIT LOG - UPDATE
        log_with_context(
            logger,
            logging.INFO,
            "Exchange rate setting updated",
            operation="UPDATE",
            setting_key=EXCHANGE_RATE_KEY,
            old_value=old_value,
            new_value=str(exchange_rate),
        )

        return existing
    else:
        # Create new record
        setting = UserSetting(
            setting_key=EXCHANGE_RATE_KEY,
            setting_value=str(exchange_rate)
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)

        # AUDIT LOG - CREATE
        log_with_context(
            logger,
            logging.INFO,
            "Exchange rate setting created",
            operation="CREATE",
            setting_key=EXCHANGE_RATE_KEY,
            setting_value=str(exchange_rate),
        )

        return setting
