from fastapi import HTTPException, status


class TransactionNotFoundError(HTTPException):
    """Exception raised when a transaction is not found."""

    def __init__(self, transaction_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id {transaction_id} not found",
        )


class InsufficientHoldingsError(HTTPException):
    """Exception raised when trying to sell more units than owned."""

    def __init__(self, isin: str, available: float, requested: float):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient holdings for {isin}. "
                f"Available: {available}, Requested: {requested}"
            ),
        )


class InvalidISINError(HTTPException):
    """Exception raised when ISIN format is invalid."""

    def __init__(self, isin: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ISIN format: {isin}",
        )


class PositionValueNotFoundError(HTTPException):
    """Exception raised when a position value is not found."""

    def __init__(self, isin: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position value for ISIN {isin} not found",
        )
