"""AWS Lambda entry point for the FastAPI application.

Mangum adapts the ASGI FastAPI app to the Lambda event/context interface.
Database migrations are run at CI/CD deploy time via `alembic upgrade head`,
not at Lambda cold start.
"""

import logging
from pathlib import Path

from mangum import Mangum

from app.config import settings
from app.main import app
from app.services.etf_breakdown_service import load_breakdowns

logger = logging.getLogger(__name__)

# Load ETF breakdown data once at cold start (lifespan="off" means the FastAPI
# startup hook doesn't run, so we load explicitly here instead)
_etf_data_dir = Path(settings.etf_data_dir)
if _etf_data_dir.exists():
    load_breakdowns(_etf_data_dir)
else:
    logger.warning("ETF data directory not found: %s", _etf_data_dir)

_mangum_handler = Mangum(app, lifespan="off")


def handler(event: dict, context: object) -> dict:
    """Lambda entry point. Delegates to Mangum (FastAPI ASGI adapter)."""
    return _mangum_handler(event, context)
