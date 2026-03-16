from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,
)


# Configure SQLite pragmas on every new connection
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configure SQLite pragmas for local dev and Lambda/EFS compatibility.

    WAL mode is NOT used: it requires POSIX shared memory which is unsupported
    on NFS (EFS), causing intermittent database corruption. The default DELETE
    journal mode is safe on both local disk and NFS.

    busy_timeout prevents immediate "database is locked" errors when multiple
    connections (or Lambda instances) compete for a write lock.
    """
    if "sqlite" in settings.database_url:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=DELETE")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
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
