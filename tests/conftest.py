"""Shared test fixtures for the test suite.

This module provides database fixtures and other shared test utilities.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from psychrag.data.database import Base

# Import models to ensure they are registered with Base
from psychrag.data.models.prompt_template import PromptTemplate  # noqa: F401


@pytest.fixture(scope="function")
def engine():
    """Create in-memory SQLite engine for tests.

    Each test gets a fresh database. The engine is torn down after
    the test completes.

    Only creates tables that are SQLite-compatible (excludes models with
    PostgreSQL-specific types like JSONB).

    Yields:
        SQLAlchemy Engine instance with compatible tables created.
    """
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")

    # Create only the prompt_templates table (SQLite-compatible)
    # Avoid creating all tables since some models use Postgres-specific types (JSONB)
    PromptTemplate.__table__.create(engine, checkfirst=True)

    yield engine

    # Cleanup: drop the table
    PromptTemplate.__table__.drop(engine, checkfirst=True)
    engine.dispose()


@pytest.fixture(scope="function")
def session(engine) -> Session:
    """Create database session for tests with automatic rollback.

    Each test gets a fresh session connected to the test database.
    After the test completes, all changes are rolled back to ensure
    test isolation.

    Args:
        engine: The test database engine fixture.

    Yields:
        SQLAlchemy Session instance.
    """
    # Create a session factory bound to the test engine
    TestingSessionLocal = sessionmaker(bind=engine)

    # Create a new session for this test
    session = TestingSessionLocal()

    yield session

    # Cleanup: rollback any changes and close the session
    session.rollback()
    session.close()
