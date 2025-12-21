"""Other asset service for business logic."""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.constants import AssetType, Currency
from app.exceptions import OtherAssetNotFoundError
from app.logging_config import log_with_context
from app.models.other_asset import OtherAsset
from app.schemas.other_asset import OtherAssetCreate
from app.services import cost_basis_service, user_setting_service

logger = logging.getLogger(__name__)


def upsert_other_asset(db: Session, asset_data: OtherAssetCreate) -> OtherAsset:
    """
    Create or update an other asset (UPSERT operation).

    If (asset_type, asset_detail) exists, updates the value and updated_at.
    If it doesn't exist, creates a new record.

    Note: Cannot create or update 'investments' type (validated in schema).

    Args:
        db: Database session
        asset_data: Other asset data

    Returns:
        Created or updated other asset
    """
    # Check if asset exists with this (asset_type, asset_detail) combination
    existing = (
        db.query(OtherAsset)
        .filter(
            OtherAsset.asset_type == asset_data.asset_type.value,
            OtherAsset.asset_detail == asset_data.asset_detail,
        )
        .first()
    )

    if existing:
        # Update existing record
        # Track changes
        changes = {}
        if existing.currency != asset_data.currency.value:
            changes["currency"] = {
                "before": existing.currency,
                "after": asset_data.currency.value,
            }
        if existing.value != asset_data.value:
            changes["value"] = {
                "before": str(existing.value),
                "after": str(asset_data.value),
            }

        existing.currency = asset_data.currency.value
        existing.value = asset_data.value
        # updated_at will auto-update via onupdate in model
        db.commit()
        db.refresh(existing)

        # AUDIT LOG - UPDATE
        log_with_context(
            logger,
            logging.INFO,
            "Other asset updated",
            operation="UPSERT_UPDATE",
            asset_type=asset_data.asset_type.value,
            asset_detail=asset_data.asset_detail,
            changes=changes,
        )

        return existing
    else:
        # Create new record
        other_asset = OtherAsset(
            asset_type=asset_data.asset_type.value,
            asset_detail=asset_data.asset_detail,
            currency=asset_data.currency.value,
            value=asset_data.value,
        )
        db.add(other_asset)
        db.commit()
        db.refresh(other_asset)

        # AUDIT LOG - CREATE
        log_with_context(
            logger,
            logging.INFO,
            "Other asset created",
            operation="UPSERT_CREATE",
            asset_type=asset_data.asset_type.value,
            asset_detail=asset_data.asset_detail,
            currency=asset_data.currency.value,
            value=str(asset_data.value),
        )

        return other_asset


def get_other_asset(db: Session, asset_type: str, asset_detail: str | None = None) -> OtherAsset:
    """
    Get an other asset by asset_type and asset_detail.

    Args:
        db: Database session
        asset_type: Asset type (e.g., 'crypto', 'cash_eur')
        asset_detail: Asset detail (account name for cash, None for others)

    Returns:
        Other asset

    Raises:
        OtherAssetNotFoundError: If asset not found
    """
    other_asset = (
        db.query(OtherAsset)
        .filter(OtherAsset.asset_type == asset_type, OtherAsset.asset_detail == asset_detail)
        .first()
    )

    if not other_asset:
        raise OtherAssetNotFoundError(asset_type, asset_detail)

    return other_asset


def get_all_other_assets(db: Session) -> list[OtherAsset]:
    """
    Get all other assets from the database.

    Does NOT include synthetic investments row.
    Ordered by asset_type, then asset_detail.

    Args:
        db: Database session

    Returns:
        List of all other assets
    """
    return (
        db.query(OtherAsset)
        .order_by(OtherAsset.asset_type.asc(), OtherAsset.asset_detail.asc())
        .all()
    )


def get_all_other_assets_with_investments(db: Session) -> tuple[list[OtherAsset], Decimal]:
    """
    Get all other assets including synthetic 'investments' row with EUR conversion metadata.

    The investments row is computed from portfolio summary and represents
    the total current value of the ETF portfolio. It is NOT stored in the
    database but generated on-the-fly.

    Returns assets in order: investments first, then others sorted by type/detail.
    Each asset has the exchange_rate attached as _exchange_rate for computed field access.

    Args:
        db: Database session

    Returns:
        Tuple of (assets list with synthetic investments row first, exchange_rate_used)
    """
    # Get exchange rate from settings (default 25.00)
    exchange_rate = user_setting_service.get_exchange_rate_setting(db) or Decimal("25.00")

    # Get portfolio summary to extract total current invested value
    portfolio_summary = cost_basis_service.get_portfolio_summary(db)

    # Extract total current portfolio value
    # This is the sum of all position current_values from the holdings
    investments_value = Decimal("0")
    if portfolio_summary.holdings:
        for holding in portfolio_summary.holdings:
            if holding.current_value is not None:
                investments_value += holding.current_value

    # Create synthetic investments row (id=0 as marker)
    investments_asset = OtherAsset(
        id=0,
        asset_type=AssetType.INVESTMENTS.value,
        asset_detail=None,
        currency=Currency.EUR.value,
        value=investments_value,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Get all real assets from database
    real_assets = get_all_other_assets(db)

    # Attach exchange rate to all assets for computed_field access
    all_assets = [investments_asset] + real_assets
    for asset in all_assets:
        asset.exchange_rate_ = exchange_rate

    # Return assets and exchange rate used
    return all_assets, exchange_rate


def delete_other_asset(db: Session, asset_type: str, asset_detail: str | None = None) -> None:
    """
    Delete an other asset by asset_type and asset_detail.

    Args:
        db: Database session
        asset_type: Asset type
        asset_detail: Asset detail (account name for cash, None for others)

    Raises:
        OtherAssetNotFoundError: If asset not found
    """
    other_asset = get_other_asset(db, asset_type, asset_detail)

    # Store for audit log
    deleted_data = {
        "asset_type": other_asset.asset_type,
        "asset_detail": other_asset.asset_detail,
        "currency": other_asset.currency,
        "value": str(other_asset.value),
    }

    db.delete(other_asset)
    db.commit()

    # AUDIT LOG
    log_with_context(
        logger,
        logging.INFO,
        "Other asset deleted",
        operation="DELETE",
        **deleted_data,
    )
