#!/usr/bin/env python3
"""One-time migration of existing SQLite data to Neon PostgreSQL.

Usage:
    cd backend
    uv run python scripts/migrate_sqlite_to_postgres.py \
        --sqlite-path /path/to/portfolio.db \
        --pg-url "postgresql://user:pass@host/neondb?sslmode=require"

Run AFTER `alembic upgrade head` on Neon. Run BEFORE the first Lambda deploy
pointing at Neon.
"""

import argparse
import sqlite3
from decimal import Decimal

import psycopg2
import psycopg2.extras

TABLES = [
    "transactions",
    "isin_metadata",
    "position_values",
    "other_assets",
    "asset_snapshots",
    "user_settings",
]


def get_sqlite_rows(sqlite_conn: sqlite3.Connection, table: str) -> tuple[list, list]:
    """Fetch all rows from a SQLite table. Returns (column_names, rows)."""
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")  # noqa: S608
    rows = cursor.fetchall()
    if not rows:
        return [], []
    columns = list(rows[0].keys())
    return columns, [dict(row) for row in rows]


def coerce_decimals(row: dict) -> dict:
    """Convert SQLite floats to Decimal for PostgreSQL Numeric columns."""
    return {
        k: Decimal(str(v)) if isinstance(v, float) else v
        for k, v in row.items()
    }


def migrate_table(
    sqlite_conn: sqlite3.Connection,
    pg_conn: psycopg2.extensions.connection,
    table: str,
) -> int:
    """Copy all rows from SQLite table to PostgreSQL. Safe to re-run (ON CONFLICT DO NOTHING)."""
    columns, rows = get_sqlite_rows(sqlite_conn, table)
    if not rows:
        print(f"  {table}: 0 rows (skipped)")
        return 0

    rows = [coerce_decimals(row) for row in rows]
    col_names = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join(f"%({c})s" for c in columns)
    sql = f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

    with pg_conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, rows, page_size=100)
        pg_conn.commit()

    print(f"  {table}: {len(rows)} rows inserted")
    return len(rows)


def reset_sequences(pg_conn: psycopg2.extensions.connection) -> None:
    """Advance PostgreSQL sequences to MAX(id) after bulk insert.

    Without this, the next INSERT from the app would try id=1 and hit a
    duplicate key error because sequences were not advanced during bulk load.
    """
    with pg_conn.cursor() as cur:
        for table in TABLES:
            cur.execute(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', 'id'),
                    COALESCE(MAX(id), 1)
                )
                FROM "{table}"
                """
            )
        pg_conn.commit()
    print("Sequences reset.")


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="Migrate SQLite → Neon PostgreSQL")
    parser.add_argument("--sqlite-path", required=True, help="Path to portfolio.db")
    parser.add_argument("--pg-url", required=True, help="PostgreSQL connection URL")
    args = parser.parse_args()

    print(f"Source: {args.sqlite_path}")
    print(f"Target: {args.pg_url[:40]}...")

    sqlite_conn = sqlite3.connect(args.sqlite_path)
    sqlite_conn.execute("PRAGMA foreign_keys=OFF")
    pg_conn = psycopg2.connect(args.pg_url)

    try:
        total = sum(migrate_table(sqlite_conn, pg_conn, t) for t in TABLES)
        reset_sequences(pg_conn)
        print(f"\nMigration complete: {total} total rows migrated.")
    except Exception as e:
        pg_conn.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    main()
