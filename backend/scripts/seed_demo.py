"""Seed a database with demo data for the demo Neon branch.

Usage:
    DEMO_DATABASE_URL="postgresql://..." uv run python scripts/seed_demo.py

If DEMO_DATABASE_URL is not set, falls back to DATABASE_URL from .env.
"""

import os
import sys
from datetime import date, datetime
from decimal import Decimal

# Add backend directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.constants import ISINType, TransactionType
from app.database import Base
from app.models.asset_snapshot import AssetSnapshot  # noqa: F401
from app.models.isin_metadata import ISINMetadata  # noqa: F401
from app.models.other_asset import OtherAsset  # noqa: F401
from app.models.position_value import PositionValue  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.user_setting import UserSetting  # noqa: F401


def get_database_url() -> str:
    """Get the database URL from DEMO_DATABASE_URL env var."""
    url = os.environ.get("DEMO_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DEMO_DATABASE_URL env var is required. "
            'Usage: DEMO_DATABASE_URL="postgresql://..." uv run python scripts/seed_demo.py'
        )
    return url


def seed(database_url: str) -> None:
    """Seed the database with demo data."""
    is_postgres = "postgresql" in database_url or "postgres://" in database_url
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        poolclass=NullPool if is_postgres else None,
    )

    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()

    try:
        # Clear existing data
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(text(f"DELETE FROM {table.name}"))
        db.commit()

        # --- ISIN Metadata ---
        isin_metadata = [
            ISINMetadata(
                isin="IE00B4L5Y983", name="iShares Core MSCI World UCITS ETF", type=ISINType.STOCK
            ),
            ISINMetadata(
                isin="IE00B4WXJJ64", name="iShares Physical Gold ETC", type=ISINType.REAL_ASSET
            ),
            ISINMetadata(isin="US0378331005", name="Apple Inc.", type=ISINType.STOCK),
        ]
        db.add_all(isin_metadata)
        db.flush()

        # --- Transactions ---
        transactions = [
            Transaction(
                date=date(2024, 2, 10),
                isin="IE00B4L5Y983",
                broker="DEGIRO",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("85.5000"),
                units=Decimal("10.0000"),
                transaction_type=TransactionType.BUY,
            ),
            Transaction(
                date=date(2024, 4, 15),
                isin="IE00B4L5Y983",
                broker="DEGIRO",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("88.2000"),
                units=Decimal("5.0000"),
                transaction_type=TransactionType.BUY,
            ),
            Transaction(
                date=date(2024, 8, 20),
                isin="IE00B4L5Y983",
                broker="DEGIRO",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("92.0000"),
                units=Decimal("3.0000"),
                transaction_type=TransactionType.SELL,
            ),
            Transaction(
                date=date(2024, 3, 5),
                isin="IE00B4WXJJ64",
                broker="DEGIRO",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("22.8000"),
                units=Decimal("20.0000"),
                transaction_type=TransactionType.BUY,
            ),
            Transaction(
                date=date(2024, 7, 12),
                isin="IE00B4WXJJ64",
                broker="DEGIRO",
                fee=Decimal("1.50"),
                price_per_unit=Decimal("23.5000"),
                units=Decimal("10.0000"),
                transaction_type=TransactionType.BUY,
            ),
            Transaction(
                date=date(2024, 1, 20),
                isin="US0378331005",
                broker="IBKR",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("182.0000"),
                units=Decimal("2.0000"),
                transaction_type=TransactionType.BUY,
            ),
            Transaction(
                date=date(2024, 6, 1),
                isin="US0378331005",
                broker="IBKR",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("195.0000"),
                units=Decimal("1.0000"),
                transaction_type=TransactionType.BUY,
            ),
            Transaction(
                date=date(2024, 9, 15),
                isin="US0378331005",
                broker="IBKR",
                fee=Decimal("2.00"),
                price_per_unit=Decimal("210.0000"),
                units=Decimal("1.0000"),
                transaction_type=TransactionType.SELL,
            ),
        ]
        db.add_all(transactions)
        db.flush()

        # --- Position Values (matching last snapshot: investments = 23500 EUR) ---
        position_values = [
            PositionValue(isin="IE00B4L5Y983", current_value=Decimal("14000.0000")),
            PositionValue(isin="IE00B4WXJJ64", current_value=Decimal("6000.0000")),
            PositionValue(isin="US0378331005", current_value=Decimal("3500.0000")),
        ]
        db.add_all(position_values)
        db.flush()

        # --- Other Assets (matching last snapshot: Mar 2025) ---
        other_assets = [
            OtherAsset(
                asset_type="cash_eur",
                asset_detail="ING Savings",
                currency="EUR",
                value=Decimal("6000.00"),
            ),
            OtherAsset(
                asset_type="cd_account",
                asset_detail=None,
                currency="CZK",
                value=Decimal("380000.00"),
            ),
            OtherAsset(
                asset_type="pension_fund",
                asset_detail=None,
                currency="EUR",
                value=Decimal("2500.00"),
            ),
        ]
        db.add_all(other_assets)
        db.flush()

        # --- User Settings ---
        user_settings = [
            UserSetting(setting_key="exchange_rate", setting_value="25.50"),
            UserSetting(setting_key="expected_return_investment", setting_value="7.00"),
            UserSetting(setting_key="expected_return_cd", setting_value="4.00"),
        ]
        db.add_all(user_settings)
        db.flush()

        # --- Asset Snapshots ---
        # Pattern inspired by real portfolio: savings phase → diversification → full allocation
        snapshot_data: list[tuple[str, str, str | None, str, str, str, str]] = [
            # 2024: diversification begins — overall upward trend, dip in Jun-Jul
            # Jan 2024 — total ~30,200
            ("2024-01-17", "cash_eur", "ING Savings", "EUR", "13000", "25.00", "13000"),
            ("2024-01-17", "cd_account", None, "CZK", "400000", "25.00", "16000"),
            ("2024-01-17", "investments", None, "EUR", "1200", "25.00", "1200"),
            # Feb 2024 — total ~31,500
            ("2024-02-17", "cash_eur", "ING Savings", "EUR", "12000", "25.10", "12000"),
            ("2024-02-17", "cd_account", None, "CZK", "420000", "25.10", "16733.07"),
            ("2024-02-17", "investments", None, "EUR", "2800", "25.10", "2800"),
            # Mar 2024 — total ~33,000
            ("2024-03-17", "cash_eur", "ING Savings", "EUR", "11500", "25.20", "11500"),
            ("2024-03-17", "cd_account", None, "CZK", "430000", "25.20", "17063.49"),
            ("2024-03-17", "investments", None, "EUR", "4500", "25.20", "4500"),
            # Apr 2024 — total ~34,500
            ("2024-04-17", "cash_eur", "ING Savings", "EUR", "11000", "25.30", "11000"),
            ("2024-04-17", "cd_account", None, "CZK", "430000", "25.30", "16996.05"),
            ("2024-04-17", "investments", None, "EUR", "6500", "25.30", "6500"),
            # May 2024 — total ~35,000
            ("2024-05-17", "cash_eur", "ING Savings", "EUR", "10500", "25.40", "10500"),
            ("2024-05-17", "cd_account", None, "CZK", "430000", "25.40", "16929.13"),
            ("2024-05-17", "investments", None, "EUR", "7600", "25.40", "7600"),
            # Jun 2024 — dip, total ~33,500
            ("2024-06-17", "cash_eur", "ING Savings", "EUR", "10000", "25.30", "10000"),
            ("2024-06-17", "cd_account", None, "CZK", "430000", "25.30", "16996.05"),
            ("2024-06-17", "investments", None, "EUR", "6500", "25.30", "6500"),
            # Jul 2024 — further dip, total ~32,000
            ("2024-07-17", "cash_eur", "ING Savings", "EUR", "9500", "25.20", "9500"),
            ("2024-07-17", "cd_account", None, "CZK", "430000", "25.20", "17063.49"),
            ("2024-07-17", "investments", None, "EUR", "5500", "25.20", "5500"),
            # Aug 2024 — recovery, total ~34,000
            ("2024-08-17", "cash_eur", "ING Savings", "EUR", "9000", "25.30", "9000"),
            ("2024-08-17", "cd_account", None, "CZK", "430000", "25.30", "16996.05"),
            ("2024-08-17", "investments", None, "EUR", "8000", "25.30", "8000"),
            # Sep 2024 — total ~36,000
            ("2024-09-17", "cash_eur", "ING Savings", "EUR", "8500", "25.40", "8500"),
            ("2024-09-17", "cd_account", None, "CZK", "430000", "25.40", "16929.13"),
            ("2024-09-17", "investments", None, "EUR", "10500", "25.40", "10500"),
            # Oct 2024 — total ~38,500
            ("2024-10-17", "cash_eur", "ING Savings", "EUR", "8000", "25.50", "8000"),
            ("2024-10-17", "cd_account", None, "CZK", "430000", "25.50", "16862.75"),
            ("2024-10-17", "investments", None, "EUR", "13500", "25.50", "13500"),
            # Nov 2024 — total ~40,000
            ("2024-11-17", "cash_eur", "ING Savings", "EUR", "7500", "25.40", "7500"),
            ("2024-11-17", "cd_account", None, "CZK", "430000", "25.40", "16929.13"),
            ("2024-11-17", "investments", None, "EUR", "15500", "25.40", "15500"),
            # Dec 2024 — total ~42,000
            ("2024-12-17", "cash_eur", "ING Savings", "EUR", "7000", "25.50", "7000"),
            ("2024-12-17", "cd_account", None, "CZK", "430000", "25.50", "16862.75"),
            ("2024-12-17", "investments", None, "EUR", "18200", "25.50", "18200"),
            # 2025: full allocation (cash_eur + cd_account + investments + pension_fund)
            # Jan 2025 — total ~43,500
            ("2025-01-17", "cash_eur", "ING Savings", "EUR", "6500", "25.50", "6500"),
            ("2025-01-17", "cd_account", None, "CZK", "400000", "25.50", "15686.27"),
            ("2025-01-17", "investments", None, "EUR", "19500", "25.50", "19500"),
            ("2025-01-17", "pension_fund", None, "EUR", "1800", "25.50", "1800"),
            # Feb 2025 — total ~45,000
            ("2025-02-17", "cash_eur", "ING Savings", "EUR", "6200", "25.40", "6200"),
            ("2025-02-17", "cd_account", None, "CZK", "400000", "25.40", "15748.03"),
            ("2025-02-17", "investments", None, "EUR", "21000", "25.40", "21000"),
            ("2025-02-17", "pension_fund", None, "EUR", "2000", "25.40", "2000"),
            # Mar 2025 — total ~47,000
            ("2025-03-17", "cash_eur", "ING Savings", "EUR", "6000", "25.50", "6000"),
            ("2025-03-17", "cd_account", None, "CZK", "380000", "25.50", "14901.96"),
            ("2025-03-17", "investments", None, "EUR", "23500", "25.50", "23500"),
            ("2025-03-17", "pension_fund", None, "EUR", "2500", "25.50", "2500"),
        ]

        snapshots = [
            AssetSnapshot(
                snapshot_date=datetime.fromisoformat(row[0]),
                asset_type=row[1],
                asset_detail=row[2],
                currency=row[3],
                value=Decimal(row[4]),
                exchange_rate=Decimal(row[5]),
                value_eur=Decimal(row[6]),
            )
            for row in snapshot_data
        ]
        db.add_all(snapshots)

        db.commit()
        print(f"Demo data seeded successfully into: {database_url[:50]}...")
        print(f"  - {len(isin_metadata)} ISIN metadata entries")
        print(f"  - {len(transactions)} transactions")
        print(f"  - {len(position_values)} position values")
        print(f"  - {len(other_assets)} other assets")
        print(f"  - {len(user_settings)} user settings")
        print(f"  - {len(snapshots)} snapshots")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    url = get_database_url()
    print(f"Seeding demo data into: {url[:50]}...")
    seed(url)
