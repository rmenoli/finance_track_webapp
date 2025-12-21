import logging

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class TransactionNotFoundError(HTTPException):
    """Exception raised when a transaction is not found."""

    def __init__(self, transaction_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id {transaction_id} not found",
        )
        # Log when exception is raised
        logger.warning(
            "Transaction not found",
            extra={"transaction_id": transaction_id}
        )


class PositionValueNotFoundError(HTTPException):
    """Exception raised when a position value is not found."""

    def __init__(self, isin: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position value for ISIN {isin} not found",
        )
        logger.warning(
            "Position value not found",
            extra={"isin": isin}
        )


class ISINMetadataNotFoundError(HTTPException):
    """Exception raised when ISIN metadata is not found."""

    def __init__(self, isin: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ISIN metadata for {isin} not found",
        )
        logger.warning(
            "ISIN metadata not found",
            extra={"isin": isin}
        )


class ISINMetadataAlreadyExistsError(HTTPException):
    """Exception raised when trying to create duplicate ISIN metadata."""

    def __init__(self, isin: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ISIN metadata for {isin} already exists",
        )
        logger.warning(
            "ISIN metadata already exists",
            extra={"isin": isin}
        )


class OtherAssetNotFoundError(HTTPException):
    """Exception raised when an other asset is not found."""

    def __init__(self, asset_type: str, asset_detail: str | None = None):
        if asset_detail:
            detail = f"Other asset with type '{asset_type}' and detail '{asset_detail}' not found"
        else:
            detail = f"Other asset with type '{asset_type}' not found"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
        logger.warning(
            "Other asset not found",
            extra={"asset_type": asset_type, "asset_detail": asset_detail}
        )
