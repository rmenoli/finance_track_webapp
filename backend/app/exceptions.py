from fastapi import HTTPException, status


class TransactionNotFoundError(HTTPException):
    """Exception raised when a transaction is not found."""

    def __init__(self, transaction_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with id {transaction_id} not found",
        )


class PositionValueNotFoundError(HTTPException):
    """Exception raised when a position value is not found."""

    def __init__(self, isin: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position value for ISIN {isin} not found",
        )


class ISINMetadataNotFoundError(HTTPException):
    """Exception raised when ISIN metadata is not found."""

    def __init__(self, isin: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ISIN metadata for {isin} not found",
        )


class ISINMetadataAlreadyExistsError(HTTPException):
    """Exception raised when trying to create duplicate ISIN metadata."""

    def __init__(self, isin: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ISIN metadata for {isin} already exists",
        )
