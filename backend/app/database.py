"""
Database engine and session factory (SQLAlchemy).
"""

import logging
from typing import Generator

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)

# Configure engine with connection pooling and pre-ping
try:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=(settings.APP_ENV == "development"),
        pool_size=settings.DB_POOL_SIZE,             # Configured pool size
        max_overflow=settings.DB_MAX_OVERFLOW,       # Configured max overflow
        pool_timeout=30,         # Timeout in seconds to wait for a connection
        pool_recycle=1800,       # Recycle connections after 30 minutes to prevent stale connections
        pool_pre_ping=True,      # Verify connection validity before using it
    )
except Exception as e:
    logger.error(f"Failed to initialize database engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a DB session.
    Includes structured error handling for database operations.
    """
    db = SessionLocal()
    try:
        yield db
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error occurred: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database operation: {e}")
        db.rollback()
        raise
    finally:
        db.close()
