"""
BharatRoad Twin - Database Setup
================================
SQLAlchemy database setup with SQLite.
Uses async-compatible engine for FastAPI.
Simple, clean setup — one file for all DB concerns.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


# ── Engine & Session ───────────────────────────────────────
# SQLite database — simple and zero-cost
# check_same_thread=False is needed for SQLite + FastAPI
engine = create_engine(
    settings.resolved_database_url,
    connect_args={"check_same_thread": False},
    echo=False,  # Set to True for SQL debugging
)

# Session factory — each request gets its own session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Base Model ─────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# ── Dependency ─────────────────────────────────────────────
def get_db():
    """
    FastAPI dependency that provides a database session.
    Automatically closes the session when the request is done.
    
    Usage in routes:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all database tables.
    Called once when the application starts.
    """
    Base.metadata.create_all(bind=engine)
