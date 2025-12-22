"""ISIN metadata API router."""

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.constants import ISINType
from app.database import get_db
from app.schemas.isin_metadata import (
    ISINMetadataCreate,
    ISINMetadataListResponse,
    ISINMetadataResponse,
    ISINMetadataUpdate,
)
from app.services import isin_metadata_service

router = APIRouter(prefix="/isin-metadata", tags=["isin-metadata"])


@router.post(
    "",
    response_model=ISINMetadataResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ISIN metadata",
    description="Create new ISIN metadata (name and type)",
)
def create_isin_metadata(
    isin_metadata: ISINMetadataCreate,
    db: Session = Depends(get_db),
) -> ISINMetadataResponse:
    """Create new ISIN metadata."""
    result = isin_metadata_service.create_isin_metadata(db, isin_metadata)
    return ISINMetadataResponse.model_validate(result)


@router.get(
    "",
    response_model=ISINMetadataListResponse,
    summary="List ISIN metadata",
    description="Get all ISIN metadata with optional filtering by type",
)
def list_isin_metadata(
    type: Optional[ISINType] = Query(None, description="Filter by asset type"),
    db: Session = Depends(get_db),
) -> ISINMetadataListResponse:
    """List all ISIN metadata with optional type filter."""
    isin_metadata_list = isin_metadata_service.get_all_isin_metadata(db, asset_type=type)

    return ISINMetadataListResponse(
        items=[
            ISINMetadataResponse.model_validate(im) for im in isin_metadata_list
        ],
        total=len(isin_metadata_list),
    )


@router.get(
    "/{isin}",
    response_model=ISINMetadataResponse,
    summary="Get ISIN metadata by ISIN",
    description="Retrieve specific ISIN metadata by ISIN code",
)
def get_isin_metadata(
    isin: str = Path(..., min_length=12, max_length=12, description="ISIN code"),
    db: Session = Depends(get_db),
) -> ISINMetadataResponse:
    """Get ISIN metadata by ISIN."""
    isin_metadata = isin_metadata_service.get_isin_metadata(db, isin)
    return ISINMetadataResponse.model_validate(isin_metadata)


@router.put(
    "/{isin}",
    response_model=ISINMetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Update ISIN metadata",
    description="Update existing ISIN metadata (name and/or type)",
)
def update_isin_metadata(
    isin: str = Path(..., min_length=12, max_length=12, description="ISIN code"),
    isin_metadata_update: ISINMetadataUpdate = ...,
    db: Session = Depends(get_db),
) -> ISINMetadataResponse:
    """Update ISIN metadata."""
    result = isin_metadata_service.update_isin_metadata(db, isin, isin_metadata_update)
    return ISINMetadataResponse.model_validate(result)


@router.delete(
    "/{isin}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ISIN metadata",
    description="Delete ISIN metadata by ISIN code",
)
def delete_isin_metadata(
    isin: str = Path(..., min_length=12, max_length=12, description="ISIN code"),
    db: Session = Depends(get_db),
) -> None:
    """Delete ISIN metadata."""
    isin_metadata_service.delete_isin_metadata(db, isin)
