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
from app.services import other_asset_service

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
    result = other_asset_service.upsert_other_asset(db, asset)
    return OtherAssetResponse.model_validate(result)


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
    if include_investments:
        other_assets = other_asset_service.get_all_other_assets_with_investments(db)
    else:
        other_assets = other_asset_service.get_all_other_assets(db)

    return OtherAssetListResponse(
        other_assets=[
            OtherAssetResponse.model_validate(asset) for asset in other_assets
        ],
        total=len(other_assets),
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
    other_asset = other_asset_service.get_other_asset(db, asset_type, asset_detail)
    return OtherAssetResponse.model_validate(other_asset)


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
