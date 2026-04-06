"""AWS Lambda entry point for the FastAPI application.

Mangum adapts the ASGI FastAPI app to the Lambda event/context interface.
Database migrations are run at CI/CD deploy time via `alembic upgrade head`,
not at Lambda cold start.
"""

import logging

from mangum import Mangum

from app.main import app

logger = logging.getLogger(__name__)

_mangum_handler = Mangum(app, lifespan="off")


def handler(event: dict, context: object) -> dict:
    """Lambda entry point. Delegates to Mangum (FastAPI ASGI adapter)."""
    return _mangum_handler(event, context)
