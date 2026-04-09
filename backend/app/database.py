import threading

from fastapi import Depends, Request
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings


def _create_engine_for_url(database_url: str) -> Engine:
    """Create a SQLAlchemy engine with appropriate config for the database type."""
    is_postgres = "postgresql" in database_url or "postgres://" in database_url
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        poolclass=NullPool if is_postgres else None,
        echo=settings.debug,
    )
    _register_sqlite_pragmas(engine, database_url)
    return engine


def _register_sqlite_pragmas(engine: Engine, database_url: str) -> None:
    """Configure SQLite pragmas on every new connection. No-op for PostgreSQL."""
    if "sqlite" not in database_url:
        return

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=DELETE")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


# Engine pool: caches one engine per unique database URL
_engine_pool: dict[str, Engine] = {}
_engine_pool_lock = threading.Lock()


def _get_engine(database_url: str) -> Engine:
    """Get or create a cached engine for the given database URL."""
    if database_url not in _engine_pool:
        with _engine_pool_lock:
            if database_url not in _engine_pool:
                _engine_pool[database_url] = _create_engine_for_url(database_url)
    return _engine_pool[database_url]


# Default engine for local dev, Alembic, and tests (only created when DATABASE_URL is set)
_default_engine = _create_engine_for_url(settings.database_url) if settings.database_url else None
SessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=_default_engine)
    if _default_engine
    else None
)

Base = declarative_base()


def _get_db_url_from_request(request: Request) -> str | None:
    """Extract database URL from request state (set by API key middleware)."""
    return getattr(request.state, "database_url", None)


def get_db(db_url: str | None = Depends(_get_db_url_from_request)):
    """Dependency function to get database session.

    If the middleware resolved an API key to a database URL,
    uses that URL's engine. Otherwise falls back to the default engine.
    """
    if db_url:
        engine = _get_engine(db_url)
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = session_factory()
    elif SessionLocal:
        db = SessionLocal()
    else:
        raise RuntimeError("No DATABASE_URL configured and no API key provided")

    try:
        yield db
    finally:
        db.close()
