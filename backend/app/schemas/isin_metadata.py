"""ISIN metadata schemas for validation and serialization."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import ISIN_PATTERN, ISINType


class ISINMetadataBase(BaseModel):
    """Base schema for ISIN metadata data."""

    isin: str = Field(..., min_length=12, max_length=12, description="ISIN code")
    name: str = Field(..., min_length=1, max_length=255, description="Asset name")
    type: ISINType = Field(..., description="Asset type (stock, bond, real-asset)")


class ISINMetadataCreate(ISINMetadataBase):
    """Schema for creating ISIN metadata."""

    @field_validator("isin")
    @classmethod
    def validate_isin(cls, v: str) -> str:
        """Validate ISIN format and normalize to uppercase."""
        if not ISIN_PATTERN.match(v.upper()):
            raise ValueError(
                "ISIN must be 12 characters: 2 letters + 9 alphanumeric + 1 digit"
            )
        return v.upper()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and normalize name (strip whitespace)."""
        return v.strip()

    model_config = ConfigDict(use_enum_values=False)


class ISINMetadataUpdate(BaseModel):
    """Schema for updating ISIN metadata (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Asset name")
    type: Optional[ISINType] = Field(None, description="Asset type (stock, bond, real-asset)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize name if provided."""
        return v.strip() if v else None

    model_config = ConfigDict(use_enum_values=False)


class ISINMetadataResponse(ISINMetadataBase):
    """Schema for ISIN metadata responses."""

    id: int = Field(..., description="ISIN metadata ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True, use_enum_values=False)


class ISINMetadataListResponse(BaseModel):
    """Schema for list of ISIN metadata."""

    items: list[ISINMetadataResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
