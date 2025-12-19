"""Other asset schemas for validation and serialization."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.constants import AssetType, Currency, VALID_ACCOUNT_NAMES


class OtherAssetBase(BaseModel):
    """Base schema for other asset data."""

    asset_type: AssetType = Field(..., description="Asset type (crypto, cash_eur, cash_czk, cd_account, pension_fund)")
    asset_detail: Optional[str] = Field(None, max_length=100, description="Asset detail (account name for cash assets, None for others)")
    currency: Currency = Field(..., description="Currency (EUR or CZK)")
    value: Decimal = Field(..., ge=0, description="Value in the specified currency")


class OtherAssetCreate(BaseModel):
    """Schema for creating/updating an other asset (UPSERT operation)."""

    asset_type: AssetType = Field(..., description="Asset type (crypto, cash_eur, cash_czk, cd_account, pension_fund)")
    asset_detail: Optional[str] = Field(None, max_length=100, description="Asset detail (account name for cash assets, None for others)")
    currency: Currency = Field(..., description="Currency (EUR or CZK)")
    value: Decimal = Field(..., ge=0, description="Value in the specified currency")

    @field_validator("asset_type")
    @classmethod
    def validate_not_investments(cls, v: AssetType) -> AssetType:
        """Prevent manual creation of investments asset type."""
        if v == AssetType.INVESTMENTS:
            raise ValueError("Cannot manually create or update 'investments' asset type. This is computed from portfolio.")
        return v

    @model_validator(mode="after")
    def validate_asset_detail_and_currency(self):
        """Validate asset_detail and currency based on asset_type."""
        asset_type = self.asset_type
        asset_detail = self.asset_detail
        currency = self.currency

        # Cash assets require account name
        if asset_type in (AssetType.CASH_EUR, AssetType.CASH_CZK):
            if not asset_detail:
                raise ValueError(f"Cash assets (type '{asset_type.value}') require an account name in 'asset_detail'")

            if asset_detail not in VALID_ACCOUNT_NAMES:
                raise ValueError(
                    f"Invalid account name '{asset_detail}'. "
                    f"Must be one of: {', '.join(sorted(VALID_ACCOUNT_NAMES))}"
                )

            # Validate currency matches asset type
            expected_currency = Currency.EUR if asset_type == AssetType.CASH_EUR else Currency.CZK
            if currency != expected_currency:
                raise ValueError(
                    f"Currency mismatch: asset type '{asset_type.value}' requires currency '{expected_currency.value}', "
                    f"but got '{currency.value}'"
                )
        else:
            # Non-cash assets must have asset_detail=None
            if asset_detail is not None:
                raise ValueError(
                    f"Non-cash assets (type '{asset_type.value}') must not have 'asset_detail'. "
                    f"Set to null/None."
                )

        return self


class OtherAssetResponse(OtherAssetBase):
    """Schema for other asset responses."""

    id: int = Field(..., description="Other asset ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class OtherAssetListResponse(BaseModel):
    """Schema for list of other assets."""

    other_assets: list[OtherAssetResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
