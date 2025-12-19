"""Other asset service for business logic."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.constants import AssetType, Currency
from app.exceptions import OtherAssetNotFoundError
from app.models.other_asset import OtherAsset
from app.schemas.other_asset import OtherAssetCreate
from app.services import cost_basis_service


def upsert_other_asset(
    db: Session,
    asset_data: OtherAssetCreate
) -> OtherAsset:
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
    existing = db.query(OtherAsset).filter(
        OtherAsset.asset_type == asset_data.asset_type.value,
        OtherAsset.asset_detail == asset_data.asset_detail
    ).first()

    if existing:
        # Update existing record
        existing.currency = asset_data.currency.value
        existing.value = asset_data.value
        # updated_at will auto-update via onupdate in model
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new record
        other_asset = OtherAsset(
            asset_type=asset_data.asset_type.value,
            asset_detail=asset_data.asset_detail,
            currency=asset_data.currency.value,
            value=asset_data.value
        )
        db.add(other_asset)
        db.commit()
        db.refresh(other_asset)
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
    other_asset = db.query(OtherAsset).filter(
        OtherAsset.asset_type == asset_type,
        OtherAsset.asset_detail == asset_detail
    ).first()

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
    return db.query(OtherAsset).order_by(
        OtherAsset.asset_type.asc(),
        OtherAsset.asset_detail.asc()
    ).all()


def get_all_other_assets_with_investments(db: Session) -> list[OtherAsset]:
    """
    Get all other assets including synthetic 'investments' row.

    The investments row is computed from portfolio summary and represents
    the total current value of the ETF portfolio. It is NOT stored in the
    database but generated on-the-fly.

    Returns assets in order: investments first, then others sorted by type/detail.

    Args:
        db: Database session

    Returns:
        List of all other assets with synthetic investments row first
    """
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
        updated_at=datetime.utcnow()
    )

    # Get all real assets from database
    real_assets = get_all_other_assets(db)

    # Return investments first, then real assets
    return [investments_asset] + real_assets


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
    db.delete(other_asset)
    db.commit()
