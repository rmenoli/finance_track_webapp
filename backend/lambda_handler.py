"""AWS Lambda entry point for the FastAPI application.

Mangum adapts the ASGI FastAPI app to the Lambda event/context interface.
Alembic migrations are run on every cold start (idempotent — safe to re-run).
"""

import logging
import os

from alembic import command
from alembic.config import Config
from mangum import Mangum

from app.main import app

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(__file__)


def _run_migrations() -> None:
    """Apply any pending Alembic migrations."""
    alembic_cfg = Config(os.path.join(_BASE_DIR, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(_BASE_DIR, "alembic"))
    command.upgrade(alembic_cfg, "head")
    logger.info("Alembic migrations applied")


# Run migrations on cold start (module-level, runs once per container)
_run_migrations()

# Mangum wraps the FastAPI ASGI app for Lambda
handler = Mangum(app, lifespan="off")
