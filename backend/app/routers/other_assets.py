"""Other assets API router."""

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.other_asset import (
    OtherAssetCreate,
    OtherAssetListResponse,
    OtherAssetResponse,
)
from app.services import other_asset_service, user_setting_service

router = APIRouter(prefix="/other-assets", tags=["other-assets"])


@router.post(
    "",
    response_model=OtherAssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update other asset",
    description="Create a new other asset or update existing one (UPSERT by asset_type and asset_detail)",
)
def upsert_other_asset(
    asset: OtherAssetCreate,
    db: Session = Depends(get_db),
) -> OtherAssetResponse:
    """Create or update an other asset."""
    from decimal import Decimal

    result = other_asset_service.upsert_other_asset(db, asset)
    exchange_rate = user_setting_service.get_exchange_rate_setting(db) or Decimal("25.00")

    return OtherAssetResponse(
        id=result.id,
        asset_type=result.asset_type,
        asset_detail=result.asset_detail,
        currency=result.currency,
        value=result.value,
        created_at=result.created_at,
        updated_at=result.updated_at,
        exchange_rate_=exchange_rate,
    )


@router.get(
    "",
    response_model=OtherAssetListResponse,
    summary="List all other assets",
    description="Get all other assets, optionally including synthetic investments row from portfolio",
)
def list_other_assets(
    include_investments: bool = Query(
        True,
        description="Include synthetic investments row computed from portfolio summary"
    ),
    db: Session = Depends(get_db),
) -> OtherAssetListResponse:
    """List all other assets."""
    from decimal import Decimal

    if include_investments:
        other_assets, exchange_rate = other_asset_service.get_all_other_assets_with_investments(db)
    else:
        other_assets = other_asset_service.get_all_other_assets(db)
        exchange_rate = user_setting_service.get_exchange_rate_setting(db) or Decimal("25.00")

    # Create response objects with exchange_rate_ set
    response_assets = []
    for asset in other_assets:
        asset_dict = {
            "id": asset.id,
            "asset_type": asset.asset_type,
            "asset_detail": asset.asset_detail,
            "currency": asset.currency,
            "value": asset.value,
            "created_at": asset.created_at,
            "updated_at": asset.updated_at,
            "exchange_rate_": exchange_rate,
        }
        response_assets.append(OtherAssetResponse(**asset_dict))

    return OtherAssetListResponse(
        other_assets=response_assets,
        total=len(response_assets),
        exchange_rate_used=exchange_rate,
    )


@router.get(
    "/{asset_type}",
    response_model=OtherAssetResponse,
    summary="Get other asset by type and detail",
    description="Retrieve a specific other asset by asset_type and optional asset_detail",
)
def get_other_asset(
    asset_type: str = Path(..., min_length=1, max_length=50, description="Asset type"),
    asset_detail: Optional[str] = Query(None, max_length=100, description="Asset detail (account name for cash)"),
    db: Session = Depends(get_db),
) -> OtherAssetResponse:
    """Get an other asset by type and detail."""
    from decimal import Decimal

    other_asset = other_asset_service.get_other_asset(db, asset_type, asset_detail)
    exchange_rate = user_setting_service.get_exchange_rate_setting(db) or Decimal("25.00")

    return OtherAssetResponse(
        id=other_asset.id,
        asset_type=other_asset.asset_type,
        asset_detail=other_asset.asset_detail,
        currency=other_asset.currency,
        value=other_asset.value,
        created_at=other_asset.created_at,
        updated_at=other_asset.updated_at,
        exchange_rate_=exchange_rate,
    )


@router.delete(
    "/{asset_type}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete other asset",
    description="Delete an other asset by asset_type and optional asset_detail",
)
def delete_other_asset(
    asset_type: str = Path(..., min_length=1, max_length=50, description="Asset type"),
    asset_detail: Optional[str] = Query(None, max_length=100, description="Asset detail (account name for cash)"),
    db: Session = Depends(get_db),
) -> None:
    """Delete an other asset."""
    other_asset_service.delete_other_asset(db, asset_type, asset_detail)
