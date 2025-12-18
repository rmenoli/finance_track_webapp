"""Tests for transaction service."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.constants import TransactionType
from app.exceptions import TransactionNotFoundError
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services import transaction_service


class TestTransactionService:
    """Test transaction service CRUD operations."""

    def test_create_transaction(self, db_session):
        """Test creating a transaction."""
        transaction_data = TransactionCreate(
            date=date.today(),
            isin="IE00B4L5Y983",
            broker="Interactive Brokers",
            fee=Decimal("1.50"),
            price_per_unit=Decimal("450.25"),
            units=Decimal("10.0"),
            transaction_type=TransactionType.BUY
        )

        transaction = transaction_service.create_transaction(db_session, transaction_data)

        assert transaction.id is not None
        assert transaction.isin == "IE00B4L5Y983"
        assert transaction.broker == "Interactive Brokers"
        assert transaction.fee == Decimal("1.50")
        assert transaction.price_per_unit == Decimal("450.25")
        assert transaction.units == Decimal("10.0")
        assert transaction.transaction_type == TransactionType.BUY
        assert transaction.created_at is not None
        assert transaction.updated_at is not None

    def test_get_transaction(self, db_session):
        """Test getting a transaction by ID."""
        # Create a transaction
        transaction_data = TransactionCreate(
            date=date.today(),
            isin="IE00B4L5Y983",
            broker="Test Broker",
            fee=Decimal("1.00"),
            price_per_unit=Decimal("100.00"),
            units=Decimal("5.0"),
            transaction_type=TransactionType.BUY
        )
        created = transaction_service.create_transaction(db_session, transaction_data)

        # Get the transaction
        retrieved = transaction_service.get_transaction(db_session, created.id)

        assert retrieved.id == created.id
        assert retrieved.isin == created.isin

    def test_get_transaction_not_found(self, db_session):
        """Test getting a non-existent transaction raises error."""
        with pytest.raises(TransactionNotFoundError):
            transaction_service.get_transaction(db_session, 999)

    def test_get_transactions_no_filters(self, db_session):
        """Test getting all transactions without filters."""
        # Create multiple transactions
        for i in range(3):
            transaction_data = TransactionCreate(
                date=date.today() - timedelta(days=i),
                isin="IE00B4L5Y983",
                broker=f"Broker {i}",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
            transaction_service.create_transaction(db_session, transaction_data)

        transactions, total = transaction_service.get_transactions(db_session)

        assert total == 3
        assert len(transactions) == 3

    def test_get_transactions_filter_by_isin(self, db_session):
        """Test filtering transactions by ISIN."""
        # Create transactions with different ISINs
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker 1",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="US0378331005",
                broker="Broker 2",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("200.00"),
                units=Decimal("10.0"),
                transaction_type=TransactionType.BUY
            )
        )

        transactions, total = transaction_service.get_transactions(
            db_session, isin="IE00B4L5Y983"
        )

        assert total == 1
        assert transactions[0].isin == "IE00B4L5Y983"

    def test_get_transactions_filter_by_broker(self, db_session):
        """Test filtering transactions by broker."""
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Interactive Brokers",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Degiro",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )

        transactions, total = transaction_service.get_transactions(
            db_session, broker="Interactive Brokers"
        )

        assert total == 1
        assert transactions[0].broker == "Interactive Brokers"

    def test_get_transactions_filter_by_type(self, db_session):
        """Test filtering transactions by type."""
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=date.today(),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("110.00"),
                units=Decimal("3.0"),
                transaction_type=TransactionType.SELL
            )
        )

        transactions, total = transaction_service.get_transactions(
            db_session, transaction_type=TransactionType.BUY
        )

        assert total == 1
        assert transactions[0].transaction_type == TransactionType.BUY

    def test_get_transactions_filter_by_date_range(self, db_session):
        """Test filtering transactions by date range."""
        today = date.today()
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=today - timedelta(days=10),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=today - timedelta(days=5),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=today,
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )

        transactions, total = transaction_service.get_transactions(
            db_session,
            start_date=today - timedelta(days=7),
            end_date=today
        )

        assert total == 2

    def test_get_transactions_pagination(self, db_session):
        """Test transaction pagination."""
        # Create 5 transactions
        for i in range(5):
            transaction_service.create_transaction(
                db_session,
                TransactionCreate(
                    date=date.today() - timedelta(days=i),
                    isin="IE00B4L5Y983",
                    broker="Broker",
                    fee=Decimal("1.00"),
                    price_per_unit=Decimal("100.00"),
                    units=Decimal("5.0"),
                    transaction_type=TransactionType.BUY
                )
            )

        # Get first 2
        transactions, total = transaction_service.get_transactions(
            db_session, skip=0, limit=2
        )
        assert total == 5
        assert len(transactions) == 2

        # Get next 2
        transactions, total = transaction_service.get_transactions(
            db_session, skip=2, limit=2
        )
        assert total == 5
        assert len(transactions) == 2

    def test_get_transactions_sorting(self, db_session):
        """Test transaction sorting."""
        today = date.today()
        # Create transactions with different dates
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=today - timedelta(days=2),
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                date=today,
                isin="IE00B4L5Y983",
                broker="Broker",
                fee=Decimal("1.00"),
                price_per_unit=Decimal("100.00"),
                units=Decimal("5.0"),
                transaction_type=TransactionType.BUY
            )
        )

        # Sort by date ascending
        transactions, _ = transaction_service.get_transactions(
            db_session, sort_by="date", sort_order="asc"
        )
        assert transactions[0].date < transactions[1].date

        # Sort by date descending
        transactions, _ = transaction_service.get_transactions(
            db_session, sort_by="date", sort_order="desc"
        )
        assert transactions[0].date > transactions[1].date

    def test_update_transaction(self, db_session):
        """Test updating a transaction."""
        # Create transaction
        transaction_data = TransactionCreate(
            date=date.today(),
            isin="IE00B4L5Y983",
            broker="Old Broker",
            fee=Decimal("1.00"),
            price_per_unit=Decimal("100.00"),
            units=Decimal("5.0"),
            transaction_type=TransactionType.BUY
        )
        created = transaction_service.create_transaction(db_session, transaction_data)

        # Update transaction
        update_data = TransactionUpdate(
            broker="New Broker",
            fee=Decimal("2.00")
        )
        updated = transaction_service.update_transaction(
            db_session, created.id, update_data
        )

        assert updated.id == created.id
        assert updated.broker == "New Broker"
        assert updated.fee == Decimal("2.00")
        assert updated.isin == created.isin  # Unchanged fields remain

    def test_update_transaction_not_found(self, db_session):
        """Test updating a non-existent transaction raises error."""
        update_data = TransactionUpdate(broker="New Broker")
        with pytest.raises(TransactionNotFoundError):
            transaction_service.update_transaction(db_session, 999, update_data)

    def test_delete_transaction(self, db_session):
        """Test deleting a transaction."""
        # Create transaction
        transaction_data = TransactionCreate(
            date=date.today(),
            isin="IE00B4L5Y983",
            broker="Broker",
            fee=Decimal("1.00"),
            price_per_unit=Decimal("100.00"),
            units=Decimal("5.0"),
            transaction_type=TransactionType.BUY
        )
        created = transaction_service.create_transaction(db_session, transaction_data)

        # Delete transaction
        transaction_service.delete_transaction(db_session, created.id)

        # Verify it's deleted
        with pytest.raises(TransactionNotFoundError):
            transaction_service.get_transaction(db_session, created.id)

    def test_delete_transaction_not_found(self, db_session):
        """Test deleting a non-existent transaction raises error."""
        with pytest.raises(TransactionNotFoundError):
            transaction_service.delete_transaction(db_session, 999)
