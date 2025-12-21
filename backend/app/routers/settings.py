"""Settings API router."""

from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user_setting import ExchangeRateResponse, ExchangeRateUpdateRequest
from app.services import user_setting_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get(
    "/exchange-rate",
    response_model=ExchangeRateResponse,
    summary="Get exchange rate",
    description="Get the stored exchange rate setting (default 25.00 if not set)",
)
def get_exchange_rate(
    db: Session = Depends(get_db),
) -> ExchangeRateResponse:
    """Get the exchange rate setting."""
    exchange_rate = user_setting_service.get_exchange_rate_setting(db)

    # Default to 25.00 if not set
    if exchange_rate is None:
        exchange_rate = Decimal("25.00")

    # Return a response-like object
    # Since we don't have a model instance when using default, we need to create the response directly
    setting = user_setting_service.get_exchange_rate_setting(db)
    if setting is None:
        # Return default without updated_at (will use current time)
        from datetime import datetime
        return ExchangeRateResponse(
            exchange_rate=exchange_rate,
            updated_at=datetime.utcnow()
        )

    # Get the actual UserSetting object to access updated_at
    from app.models.user_setting import UserSetting
    user_setting = db.query(UserSetting).filter(
        UserSetting.setting_key == user_setting_service.EXCHANGE_RATE_KEY
    ).first()

    return ExchangeRateResponse(
        exchange_rate=exchange_rate,
        updated_at=user_setting.updated_at
    )


@router.post(
    "/exchange-rate",
    response_model=ExchangeRateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update exchange rate",
    description="Create or update the exchange rate setting (UPSERT operation)",
)
def update_exchange_rate(
    request: ExchangeRateUpdateRequest,
    db: Session = Depends(get_db),
) -> ExchangeRateResponse:
    """Update the exchange rate setting."""
    user_setting = user_setting_service.update_exchange_rate_setting(
        db, request.exchange_rate
    )

    return ExchangeRateResponse(
        exchange_rate=Decimal(user_setting.setting_value),
        updated_at=user_setting.updated_at
    )
