"""AWS Lambda entry point for the FastAPI application.

Mangum adapts the ASGI FastAPI app to the Lambda event/context interface.
On cold start: downloads portfolio.db from S3 to /tmp, then runs Alembic migrations.
After write requests: uploads /tmp/portfolio.db back to S3 before returning.
"""

import logging
import os

import boto3
from alembic import command
from alembic.config import Config
from mangum import Mangum

from app.config import settings
from app.main import app

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(__file__)
_DB_LOCAL_PATH = "/tmp/portfolio.db"
_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _download_db_from_s3() -> None:
    """Download portfolio.db from S3 to /tmp on cold start.

    If the file does not exist in S3 yet (first deploy), log and continue —
    Alembic will create the schema from scratch.
    """
    s3 = boto3.client("s3")
    try:
        s3.download_file(settings.s3_bucket_db, settings.s3_db_key, _DB_LOCAL_PATH)
        logger.info(
            "Downloaded DB from S3",
            extra={"bucket": settings.s3_bucket_db, "key": settings.s3_db_key},
        )
    except s3.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            logger.info("No DB found in S3, starting with fresh database")
        else:
            raise


def _upload_db_to_s3() -> None:
    """Upload /tmp/portfolio.db to S3 after write operations."""
    s3 = boto3.client("s3")
    s3.upload_file(_DB_LOCAL_PATH, settings.s3_bucket_db, settings.s3_db_key)
    logger.info(
        "Uploaded DB to S3",
        extra={"bucket": settings.s3_bucket_db, "key": settings.s3_db_key},
    )


def _run_migrations() -> None:
    """Apply any pending Alembic migrations."""
    alembic_cfg = Config(os.path.join(_BASE_DIR, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(_BASE_DIR, "alembic"))
    command.upgrade(alembic_cfg, "head")
    logger.info("Alembic migrations applied")


# Cold start: restore DB from S3 (skipped when USE_S3=false for local dev), then migrate
if settings.use_s3:
    _download_db_from_s3()
_run_migrations()

_mangum_handler = Mangum(app, lifespan="off")


def handler(event: dict, context: object) -> dict:
    """Lambda entry point.

    Delegates to Mangum (FastAPI ASGI adapter), then syncs the SQLite DB
    back to S3 after any write operation so changes persist across invocations.
    """
    result = _mangum_handler(event, context)

    # Support both HTTP API (payload v2) and REST API (payload v1) event formats
    http_method = (
        event.get("requestContext", {}).get("http", {}).get("method", "")
        or event.get("httpMethod", "")
    )
    if settings.use_s3 and http_method.upper() in _WRITE_METHODS:
        _upload_db_to_s3()

    return result
