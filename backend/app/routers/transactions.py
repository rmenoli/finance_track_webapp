from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, TransactionType
from app.database import get_db
from app.exceptions import CSVImportError
from app.schemas.transaction import (
    CSVImportResponse,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new transaction",
    description="Create a new ETF transaction (BUY or SELL)",
)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """Create a new transaction."""
    created_transaction = transaction_service.create_transaction(db, transaction)
    return TransactionResponse.model_validate(created_transaction)


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List all transactions",
    description="List all transactions with optional filtering and pagination",
)
def list_transactions(
    isin: Optional[str] = Query(None, description="Filter by ISIN"),
    broker: Optional[str] = Query(None, description="Filter by broker name"),
    transaction_type: Optional[TransactionType] = Query(
        None, description="Filter by transaction type (BUY or SELL)"
    ),
    start_date: Optional[date] = Query(None, description="Filter from date (inclusive)"),
    end_date: Optional[date] = Query(None, description="Filter to date (inclusive)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Maximum number of records to return",
    ),
    sort_by: str = Query(
        "date", pattern="^(date|created_at)$", description="Sort by field"
    ),
    sort_order: str = Query(
        "desc", pattern="^(asc|desc)$", description="Sort order"
    ),
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    """List all transactions with optional filters."""
    transactions, total = transaction_service.get_transactions(
        db,
        isin=isin,
        broker=broker,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return TransactionListResponse(
        transactions=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get transaction by ID",
    description="Retrieve a specific transaction by its ID",
)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """Get a transaction by ID."""
    transaction = transaction_service.get_transaction(db, transaction_id)
    return TransactionResponse.model_validate(transaction)


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Update a transaction",
    description="Update an existing transaction",
)
def update_transaction(
    transaction_id: int,
    update_data: TransactionUpdate,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """Update a transaction."""
    updated_transaction = transaction_service.update_transaction(
        db, transaction_id, update_data
    )
    return TransactionResponse.model_validate(updated_transaction)


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a transaction",
    description="Delete a transaction by ID",
)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a transaction."""
    transaction_service.delete_transaction(db, transaction_id)


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    summary="Delete all transactions",
    description="Delete all transactions. WARNING: This operation cannot be undone!",
)
def delete_all_transactions(db: Session = Depends(get_db)) -> dict:
    """Delete all transactions."""
    deleted_count = transaction_service.delete_all_transactions(db)
    return {
        "message": f"Successfully deleted {deleted_count} transaction(s)",
        "deleted_count": deleted_count,
    }


@router.post(
    "/degiro-import-csv-transactions",
    response_model=CSVImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Import transactions from DEGIRO CSV",
    description="Import multiple transactions from a DEGIRO CSV export file. "
    "Returns detailed results for successful and failed imports.",
)
async def degiro_import_csv_transactions_endpoint(
    file: UploadFile = File(..., description="DEGIRO CSV file"),
    db: Session = Depends(get_db),
) -> CSVImportResponse:
    """
    Import transactions from DEGIRO CSV file.

    Expected CSV format (DEGIRO export):
    - Columns: Date, Time, Product, ISIN, Reference exchange, Venue, Quantity, Price,
               Local value, Value EUR, Exchange rate, AutoFX Fee,
               Transaction and/or third party fees EUR, Total EUR, Order ID
    - Date format: DD-MM-YYYY
    - Number format: European (comma as decimal separator)
    - Quantity: Positive = BUY, Negative = SELL

    Returns:
    - Summary of import (total, successful, failed)
    - List of successful imports with transaction IDs
    - List of failed imports with detailed error messages
    """
    # Validate file type
    if not file.filename or not file.filename.endswith(".csv"):
        raise CSVImportError("File must be a CSV file")

    # Read file content
    try:
        content = await file.read()
        csv_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise CSVImportError("File must be UTF-8 encoded")
    except Exception as e:
        raise CSVImportError(f"Failed to read file: {str(e)}")

    # Import transactions
    results = transaction_service.degiro_import_csv_transactions(
        db=db,
        csv_content=csv_content,
    )

    # Convert to response schema
    return CSVImportResponse(**results)
