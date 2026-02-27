import pytest
from sqlalchemy import text
from app.database import engine, SessionLocal

def test_database_connection():
    """
    Test that the application can successfully connect to the PostgreSQL database.
    """
    try:
        # Attempt to connect to the database and execute a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")

def test_session_creation():
    """
    Test that a database session can be created and used successfully.
    """
    try:
        # Attempt to create a session and execute a simple query
        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        assert result.scalar() == 1
    except Exception as e:
        pytest.fail(f"Session creation failed: {e}")
    finally:
        db.close()
