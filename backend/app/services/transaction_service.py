from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.constants import DEFAULT_PAGE_SIZE, TransactionType
from app.exceptions import TransactionNotFoundError
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


def create_transaction(db: Session, transaction_data: TransactionCreate) -> Transaction:
    """
    Create a new transaction.

    Args:
        db: Database session
        transaction_data: Transaction data

    Returns:
        Created transaction
    """
    transaction = Transaction(**transaction_data.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def get_transaction(db: Session, transaction_id: int) -> Transaction:
    """
    Get a transaction by ID.

    Args:
        db: Database session
        transaction_id: Transaction ID

    Returns:
        Transaction

    Raises:
        TransactionNotFoundError: If transaction not found
    """
    transaction = (
        db.query(Transaction).filter(Transaction.id == transaction_id).first()
    )
    if not transaction:
        raise TransactionNotFoundError(transaction_id)
    return transaction


def get_transactions(
    db: Session,
    isin: Optional[str] = None,
    broker: Optional[str] = None,
    transaction_type: Optional[TransactionType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
    sort_by: str = "date",
    sort_order: str = "desc",
) -> tuple[list[Transaction], int]:
    """
    Get transactions with optional filtering and pagination.

    Args:
        db: Database session
        isin: Filter by ISIN
        broker: Filter by broker
        transaction_type: Filter by transaction type (BUY or SELL)
        start_date: Filter by start date (inclusive)
        end_date: Filter by end date (inclusive)
        skip: Number of records to skip
        limit: Maximum number of records to return
        sort_by: Field to sort by (date or created_at)
        sort_order: Sort order (asc or desc)

    Returns:
        Tuple of (list of transactions, total count)
    """
    query = db.query(Transaction)

    # Apply filters
    if isin:
        query = query.filter(Transaction.isin == isin.upper())
    if broker:
        query = query.filter(Transaction.broker == broker)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    # Get total count
    total = query.count()

    # Apply sorting
    sort_field = Transaction.date if sort_by == "date" else Transaction.created_at
    if sort_order == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())

    # Apply pagination
    transactions = query.offset(skip).limit(limit).all()

    return transactions, total


def update_transaction(
    db: Session, transaction_id: int, update_data: TransactionUpdate
) -> Transaction:
    """
    Update a transaction.

    Args:
        db: Database session
        transaction_id: Transaction ID
        update_data: Update data

    Returns:
        Updated transaction

    Raises:
        TransactionNotFoundError: If transaction not found
    """
    transaction = get_transaction(db, transaction_id)

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, transaction_id: int) -> None:
    """
    Delete a transaction.

    Args:
        db: Database session
        transaction_id: Transaction ID

    Raises:
        TransactionNotFoundError: If transaction not found
    """
    transaction = get_transaction(db, transaction_id)
    db.delete(transaction)
    db.commit()


def get_total_transactions_count(db: Session) -> int:
    """
    Get total number of transactions.

    Args:
        db: Database session

    Returns:
        Total count
    """
    return db.query(func.count(Transaction.id)).scalar()
