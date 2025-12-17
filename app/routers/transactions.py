from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, TransactionType
from app.database import get_db
from app.schemas.transaction import (
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
