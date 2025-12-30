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


def calculate_monthly_expected_return(value: Decimal, annual_rate_percentage: Decimal) -> Decimal:
    """
    Calculate monthly expected return.

    Args:
        value: Asset value in EUR
        annual_rate_percentage: Annual return rate as percentage (e.g., 7.00 for 7%)

    Returns:
        Monthly expected return in EUR (rounded to 2 decimal places)

    Example:
        calculate_monthly_expected_return(Decimal("1000.00"), Decimal("7.00"))
        # Returns: Decimal("5.83")  # (1000 * 0.07) / 12
    """
    if value == 0 or annual_rate_percentage == 0:
        return Decimal("0.00")

    monthly_return = (value * annual_rate_percentage / 100) / 12
    return monthly_return.quantize(Decimal("0.01"))


def get_all_other_assets_with_investments(
    db: Session,
) -> tuple[list[OtherAsset], Decimal, Decimal, Decimal]:
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
        Tuple of (assets_list, exchange_rate, monthly_return_investment, monthly_return_cd)
    """
    # Get exchange rate from settings (default 25.00)
    setting = user_setting_service.get_exchange_rate_setting(db)
    exchange_rate = Decimal(setting.setting_value) if setting else Decimal("25.00")

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

    # Calculate monthly expected returns
    # 1. Get expected return settings
    investment_setting = user_setting_service.get_expected_return_investment_setting(db)
    cd_setting = user_setting_service.get_expected_return_cd_setting(db)

    investment_rate = (
        Decimal(investment_setting.setting_value) if investment_setting else Decimal("7.00")
    )
    cd_rate = Decimal(cd_setting.setting_value) if cd_setting else Decimal("4.00")

    # 2. Extract investment value from synthetic row (first in list, id=0)
    investment_value = (
        all_assets[0].value if all_assets and all_assets[0].id == 0 else Decimal("0.00")
    )

    # 3. Sum all cd_account values in EUR
    cd_total_value_eur = Decimal("0.00")
    for asset in all_assets:
        if asset.asset_type == AssetType.CD_ACCOUNT.value:
            # Convert to EUR if needed (CD accounts are typically in CZK)
            if asset.currency == Currency.EUR.value:
                cd_total_value_eur += asset.value
            else:  # CZK
                cd_total_value_eur += asset.value / exchange_rate

    # 4. Calculate monthly returns (in EUR)
    monthly_return_investment = calculate_monthly_expected_return(investment_value, investment_rate)
    monthly_return_cd = calculate_monthly_expected_return(cd_total_value_eur, cd_rate)

    # Return assets, exchange rate, and monthly returns
    return all_assets, exchange_rate, monthly_return_investment, monthly_return_cd


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
