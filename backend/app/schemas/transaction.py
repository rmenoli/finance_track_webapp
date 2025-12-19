from datetime import date as DateType
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.constants import ISIN_PATTERN, TransactionType


class TransactionBase(BaseModel):
    """Base schema for transaction data."""

    date: DateType = Field(..., description="Date of the transaction")
    isin: str = Field(..., min_length=12, max_length=12, description="ISIN code")
    broker: str = Field(..., min_length=1, max_length=100, description="Broker name")
    fee: Decimal = Field(default=Decimal("0.00"), ge=0, description="Transaction fee")
    price_per_unit: Decimal = Field(..., gt=0, description="Price per unit")
    units: Decimal = Field(..., gt=0, description="Number of units")
    transaction_type: TransactionType = Field(..., description="BUY or SELL")

    @field_validator("isin")
    @classmethod
    def validate_isin(cls, v: str) -> str:
        """Validate ISIN format."""
        if not ISIN_PATTERN.match(v.upper()):
            raise ValueError(
                "ISIN must be 12 characters: 2 letters + 9 alphanumeric + 1 digit"
            )
        return v.upper()

    @field_validator("date")
    @classmethod
    def validate_date_not_future(cls, v: DateType) -> DateType:
        """Validate that transaction date is not in the future."""
        today = DateType.today()
        if v > today:
            raise ValueError("Transaction date cannot be in the future")
        return v

    model_config = ConfigDict(use_enum_values=False)


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""

    pass


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction (all fields optional)."""

    date: Optional[DateType] = Field(None, description="Date of the transaction")
    isin: Optional[str] = Field(
        None, min_length=12, max_length=12, description="ISIN code"
    )
    broker: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Broker name"
    )
    fee: Optional[Decimal] = Field(None, ge=0, description="Transaction fee")
    price_per_unit: Optional[Decimal] = Field(None, gt=0, description="Price per unit")
    units: Optional[Decimal] = Field(None, gt=0, description="Number of units")
    transaction_type: Optional[TransactionType] = Field(
        None, description="BUY or SELL"
    )

    @field_validator("isin")
    @classmethod
    def validate_isin(cls, v: Optional[str]) -> Optional[str]:
        """Validate ISIN format if provided."""
        if v is not None and not ISIN_PATTERN.match(v.upper()):
            raise ValueError(
                "ISIN must be 12 characters: 2 letters + 9 alphanumeric + 1 digit"
            )
        return v.upper() if v else None

    @field_validator("date")
    @classmethod
    def validate_date_not_future(cls, v: Optional[DateType]) -> Optional[DateType]:
        """Validate that transaction date is not in the future."""
        if v is not None:
            today = DateType.today()
            if v > today:
                raise ValueError("Transaction date cannot be in the future")
        return v

    model_config = ConfigDict(use_enum_values=False)


class TransactionResponse(TransactionBase):
    """Schema for transaction responses."""

    id: int = Field(..., description="Transaction ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @computed_field
    @property
    def total_without_fees(self) -> Decimal:
        """Calculate total without fees (units × price_per_unit)."""
        return self.units * self.price_per_unit

    @computed_field
    @property
    def total_with_fees(self) -> Decimal:
        """Calculate total with fees (total_without_fees + fee)."""
        return self.total_without_fees + self.fee

    model_config = ConfigDict(from_attributes=True, use_enum_values=False)


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list responses."""

    transactions: list[TransactionResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
