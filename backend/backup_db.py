#!/usr/bin/env python3
"""Simplified SQLite database backup to S3 with hot backup and compression.

This script creates a safe backup of the SQLite database, compresses it,
and uploads it to S3. Old backups are managed via S3 Lifecycle Policies.

Usage:
    export S3_BUCKET=your-bucket-name
    python3 backup_db.py

AWS Authentication:
    Uses boto3's automatic credential discovery.
    For EC2: Attach IAM role with S3 permissions (recommended).
    For local: Configure ~/.aws/credentials or set AWS_* env vars.
"""

import gzip
import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import boto3


def backup_and_upload_to_s3(db_path: str, bucket_name: str, s3_prefix: str = "backups/") -> str:
    """Create hot backup of SQLite database, compress it, and upload to S3.

    Args:
        db_path: Path to SQLite database file
        bucket_name: S3 bucket name
        s3_prefix: S3 key prefix (default: "backups/")

    Returns:
        S3 key of uploaded backup

    Raises:
        FileNotFoundError: If database file doesn't exist
        Exception: If backup, compression, or upload fails

    AWS Authentication:
        boto3 automatically discovers credentials via:
        1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        2. AWS credentials file (~/.aws/credentials)
        3. IAM instance role (recommended for EC2 - no config needed)
    """
    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"portfolio_{timestamp}.db.gz"
    s3_key = f"{s3_prefix}{backup_filename}"

    # Create temporary files for backup
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        temp_db_path = temp_db.name

    with tempfile.NamedTemporaryFile(suffix=".db.gz", delete=False) as temp_gz:
        temp_gz_path = temp_gz.name

    try:
        # Step 1: Hot backup (safe - doesn't lock database)
        print(f"Creating hot backup of {db_path}...")
        source_conn = sqlite3.connect(db_path)
        backup_conn = sqlite3.connect(temp_db_path)

        with backup_conn:
            source_conn.backup(backup_conn)

        source_conn.close()
        backup_conn.close()
        print(f"Backup created: {temp_db_path}")

        # Step 2: Compress
        print("Compressing backup...")
        with open(temp_db_path, "rb") as f_in:
            with gzip.open(temp_gz_path, "wb") as f_out:
                f_out.writelines(f_in)

        size_mb = Path(temp_gz_path).stat().st_size / (1024 * 1024)
        print(f"Compressed: {size_mb:.2f} MB")

        # Step 3: Upload to S3
        print(f"Uploading to s3://{bucket_name}/{s3_key}...")
        s3_client = boto3.client("s3")
        s3_client.upload_file(temp_gz_path, bucket_name, s3_key)
        print(f"Upload complete: {s3_key}")

        return s3_key

    finally:
        # Clean up temp files
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        if os.path.exists(temp_gz_path):
            os.remove(temp_gz_path)


if __name__ == "__main__":
    # Configuration
    DB_PATH = os.path.join(os.path.dirname(__file__), "portfolio.db")
    BUCKET_NAME = "your-s3-bucket-name"

    try:
        print("=" * 60)
        print("SQLite Database Backup to S3")
        print(f"Database: {DB_PATH}")
        print(f"S3 Bucket: {BUCKET_NAME}")
        print("=" * 60)

        s3_key = backup_and_upload_to_s3(DB_PATH, BUCKET_NAME)

        print("=" * 60)
        print(f"Backup successful: s3://{BUCKET_NAME}/{s3_key}")
        print("=" * 60)

    except Exception as e:
        print(f"ERROR: Backup failed: {e}")
        exit(1)
