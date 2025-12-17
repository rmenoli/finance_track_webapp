from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,
)


# Enable WAL mode and foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configure SQLite for better performance and referential integrity."""
    if "sqlite" in settings.database_url:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()


# Dependency for FastAPI routes
def get_db():
    """
    Dependency function to get database session.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
