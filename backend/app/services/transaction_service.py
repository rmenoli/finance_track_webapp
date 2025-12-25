import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.constants import DEFAULT_PAGE_SIZE, TransactionType
from app.exceptions import (
    CSVImportError,
    PositionValueNotFoundError,
    TransactionNotFoundError,
)
from app.logging_config import log_with_context
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services import cost_basis_service, position_value_service

logger = logging.getLogger(__name__)


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

    # AUDIT LOG
    log_with_context(
        logger,
        logging.INFO,
        "Transaction created",
        operation="CREATE",
        transaction_id=transaction.id,
        isin=transaction.isin,
        transaction_type=transaction.transaction_type.value,
        units=str(transaction.units),
        price_per_unit=str(transaction.price_per_unit),
        fee=str(transaction.fee),
        broker=transaction.broker,
        date=str(transaction.date),
    )

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

    # Store before values for audit log
    before_values = {
        "isin": transaction.isin,
        "transaction_type": transaction.transaction_type.value,
        "units": str(transaction.units),
        "price_per_unit": str(transaction.price_per_unit),
        "fee": str(transaction.fee),
        "broker": transaction.broker,
        "date": str(transaction.date),
    }

    # Calculate units before update to detect reopening
    cost_basis_before = cost_basis_service.calculate_cost_basis(db, original_isin)
    units_before = cost_basis_before.total_units if cost_basis_before else Decimal("0")

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)

    # AUDIT LOG
    after_values = {
        "isin": transaction.isin,
        "transaction_type": transaction.transaction_type.value,
        "units": str(transaction.units),
        "price_per_unit": str(transaction.price_per_unit),
        "fee": str(transaction.fee),
        "broker": transaction.broker,
        "date": str(transaction.date),
    }

    changed_fields = {
        k: {"before": before_values[k], "after": after_values[k]}
        for k in before_values
        if before_values[k] != after_values[k]
    }

    log_with_context(
        logger,
        logging.INFO,
        "Transaction updated",
        operation="UPDATE",
        transaction_id=transaction.id,
        changed_fields=changed_fields,
    )

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

    # Store values for audit log before deletion
    deleted_values = {
        "transaction_id": transaction.id,
        "isin": transaction.isin,
        "transaction_type": transaction.transaction_type.value,
        "units": str(transaction.units),
        "price_per_unit": str(transaction.price_per_unit),
        "fee": str(transaction.fee),
        "broker": transaction.broker,
        "date": str(transaction.date),
    }

    # Calculate units before deletion to detect reopening
    cost_basis_before = cost_basis_service.calculate_cost_basis(db, isin_to_check)
    units_before = cost_basis_before.total_units if cost_basis_before else Decimal("0")

    db.delete(transaction)
    db.commit()

    # AUDIT LOG
    log_with_context(
        logger,
        logging.INFO,
        "Transaction deleted",
        operation="DELETE",
        **deleted_values,
    )

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
    except Exception as e:
        # LOG ERROR - previously silent
        log_with_context(
            logger,
            logging.ERROR,
            "Error during position value cleanup",
            isin=isin,
            error_type=type(e).__name__,
            error_message=str(e),
        )
        # Still don't block transaction operations
        pass


def degiro_import_csv_transactions(db: Session, csv_content: str) -> dict:
    """
    Import transactions from DEGIRO CSV file.

    Args:
        db: Database session
        csv_content: CSV file content as string

    Returns:
        Dictionary with import results:
        {
            "total_rows": int,
            "successful": int,
            "failed": int,
            "results": [{"row": int, "transaction_id": int, ...}],
            "errors": [{"row": int, "errors": [...], ...}]
        }

    Raises:
        CSVImportError: If CSV format is invalid or required columns missing
    """
    from pydantic import ValidationError

    from app.services.csv_parser import parse_degiro_csv

    results = {
        "total_rows": 0,
        "successful": 0,
        "failed": 0,
        "results": [],
        "errors": [],
    }

    try:
        # Parse CSV
        parsed_rows = parse_degiro_csv(csv_content)
        results["total_rows"] = len(parsed_rows)

        log_with_context(
            logger,
            logging.INFO,
            "Starting DEGIRO CSV import",
            total_rows=len(parsed_rows),
        )

    except ValueError as e:
        # File-level parsing error
        log_with_context(
            logger,
            logging.ERROR,
            "CSV parsing failed",
            error=str(e),
        )
        raise CSVImportError(str(e))

    # Process each row
    for row_data in parsed_rows:
        try:
            # Create TransactionCreate schema for validation
            transaction_create = TransactionCreate(
                date=row_data.date,
                isin=row_data.isin,
                broker="DEGIRO",  # Always DEGIRO for CSV imports
                fee=row_data.fee,
                price_per_unit=row_data.price,
                units=row_data.quantity,
                transaction_type=row_data.transaction_type,
            )

            # Create transaction (reuse existing service function)
            transaction = create_transaction(db, transaction_create)

            # Record success
            results["successful"] += 1
            results["results"].append({
                "row": row_data.row_number,
                "transaction_id": transaction.id,
                "isin": transaction.isin,
                "transaction_type": transaction.transaction_type,
            })

        except ValidationError as e:
            # Pydantic validation error
            results["failed"] += 1
            error_messages = [f"{err['loc'][-1]}: {err['msg']}" for err in e.errors()]
            results["errors"].append({
                "row": row_data.row_number,
                "isin": row_data.isin,
                "date": str(row_data.date),
                "errors": error_messages,
                "raw_data": row_data.raw_row,
            })

            log_with_context(
                logger,
                logging.WARNING,
                "Transaction validation failed",
                row=row_data.row_number,
                isin=row_data.isin,
                errors=error_messages,
            )

        except Exception as e:
            # Unexpected error
            results["failed"] += 1
            results["errors"].append({
                "row": row_data.row_number,
                "isin": row_data.isin if hasattr(row_data, "isin") else None,
                "date": str(row_data.date) if hasattr(row_data, "date") else None,
                "errors": [f"Unexpected error: {str(e)}"],
                "raw_data": row_data.raw_row if hasattr(row_data, "raw_row") else None,
            })

            log_with_context(
                logger,
                logging.ERROR,
                "Unexpected error during CSV import",
                row=row_data.row_number,
                error_type=type(e).__name__,
                error=str(e),
            )

    # Final summary log
    log_with_context(
        logger,
        logging.INFO,
        "DEGIRO CSV import completed",
        total_rows=results["total_rows"],
        successful=results["successful"],
        failed=results["failed"],
        success_rate=(
            f"{(results['successful'] / results['total_rows'] * 100) if results['total_rows'] > 0 else 0:.2f}%"
        ),
    )

    return results


def delete_all_transactions(db: Session) -> int:
    """
    Delete all transactions from the database.

    WARNING: This is a destructive operation that cannot be undone.

    Args:
        db: Database session

    Returns:
        Number of transactions deleted

    Raises:
        Exception: If database operation fails
    """
    try:
        # Get count before deletion
        count = db.query(Transaction).count()

        # Delete all transactions
        db.query(Transaction).delete()
        db.commit()

        # AUDIT LOG
        log_with_context(
            logger,
            logging.WARNING,
            "All transactions deleted",
            operation="BULK_DELETE",
            deleted_count=count,
        )

        return count

    except Exception as e:
        db.rollback()
        log_with_context(
            logger,
            logging.ERROR,
            "Failed to delete all transactions",
            operation="BULK_DELETE",
            error=str(e),
        )
        raise
