"""
Database connection and session management.

This module provides SQLAlchemy engine and session factory for PostgreSQL.
"""

import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

# Load environment variables
load_dotenv()

# Database configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "psych_rag")
POSTGRES_APP_USER = os.getenv("POSTGRES_APP_USER", "psych_rag_app_user")
POSTGRES_APP_PASSWORD = os.getenv("POSTGRES_APP_PASSWORD", "psych_rag_secure_password")

# Build database URL
DATABASE_URL = (
    f"postgresql+psycopg://{POSTGRES_APP_USER}:{POSTGRES_APP_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base class for declarative models
Base = declarative_base()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.

    Usage:
        with get_session() as session:
            session.add(some_object)
            session.commit()

    Yields:
        SQLAlchemy Session object.
    """
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_admin_database_url() -> str:
    """
    Get database URL using admin credentials.

    Returns:
        PostgreSQL connection URL for admin user.
    """
    admin_user = os.getenv("POSTGRES_ADMIN_USER", "postgres")
    admin_password = os.getenv("POSTGRES_ADMIN_PASSWORD", "postgres")

    return (
        f"postgresql+psycopg://{admin_user}:{admin_password}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/postgres"
    )
