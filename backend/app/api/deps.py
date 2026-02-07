"""
API Dependencies
"""
from typing import Generator
from app.db.session import SessionLocal

def get_db() -> Generator:
    """
    Database dependency for FastAPI endpoints.
    Provides a database session and ensures proper cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
