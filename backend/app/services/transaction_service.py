from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.constants import DEFAULT_PAGE_SIZE, TransactionType
from app.exceptions import PositionValueNotFoundError, TransactionNotFoundError
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services import cost_basis_service, position_value_service


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
    Update a transaction and clean up position values if needed.

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
    original_isin = transaction.isin

    # Calculate units before update to detect reopening
    cost_basis_before = cost_basis_service.calculate_cost_basis(db, original_isin)
    units_before = cost_basis_before.total_units if cost_basis_before else Decimal("0")

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)

    # Track if ISIN changed
    isin_changed = transaction.isin != original_isin

    # Cleanup current ISIN if position closed
    _cleanup_position_value_for_closed_position(db, transaction.isin)

    # Cleanup original ISIN if changed
    if isin_changed:
        _cleanup_position_value_for_closed_position(db, original_isin)

    # Check for reopening on current ISIN
    if units_before == 0:
        cost_basis_after = cost_basis_service.calculate_cost_basis(db, transaction.isin)
        units_after = cost_basis_after.total_units if cost_basis_after else Decimal("0")
        if units_after > 0:
            try:
                position_value_service.delete_position_value(db, transaction.isin)
            except PositionValueNotFoundError:
                pass

    return transaction


def delete_transaction(db: Session, transaction_id: int) -> None:
    """
    Delete a transaction and clean up position values if needed.

    Args:
        db: Database session
        transaction_id: Transaction ID

    Raises:
        TransactionNotFoundError: If transaction not found
    """
    transaction = get_transaction(db, transaction_id)
    isin_to_check = transaction.isin

    # Calculate units before deletion to detect reopening
    cost_basis_before = cost_basis_service.calculate_cost_basis(db, isin_to_check)
    units_before = cost_basis_before.total_units if cost_basis_before else Decimal("0")

    db.delete(transaction)
    db.commit()

    # Cleanup if position closed
    _cleanup_position_value_for_closed_position(db, isin_to_check)

    # Also cleanup if position reopened (was 0, now positive)
    if units_before == 0:
        cost_basis_after = cost_basis_service.calculate_cost_basis(db, isin_to_check)
        units_after = cost_basis_after.total_units if cost_basis_after else Decimal("0")
        if units_after > 0:
            # Position reopened - delete stale position value
            try:
                position_value_service.delete_position_value(db, isin_to_check)
            except PositionValueNotFoundError:
                pass


def _cleanup_position_value_for_closed_position(db: Session, isin: str) -> None:
    """
    Delete position value if the position is closed (total_units == 0).

    Called after transaction operations to maintain consistency.
    Silently handles errors - cleanup failure should not block transactions.

    Args:
        db: Database session
        isin: ISIN code to check
    """
    try:
        cost_basis = cost_basis_service.calculate_cost_basis(db, isin)

        # If position is closed, delete the position value
        if cost_basis and cost_basis.total_units == 0:
            try:
                position_value_service.delete_position_value(db, isin)
            except PositionValueNotFoundError:
                # Expected - position value doesn't exist
                pass
    except Exception:
        # Silent failure - don't block transaction operations
        pass
