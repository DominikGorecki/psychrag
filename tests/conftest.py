"""Shared test fixtures for the test suite.

This module provides database fixtures and other shared test utilities.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from psychrag.data.database import Base


@pytest.fixture(scope="function")
def engine():
    """Create in-memory SQLite engine for tests.

    Each test gets a fresh database. The engine is torn down after
    the test completes.

    Yields:
        SQLAlchemy Engine instance with all tables created.
    """
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")

    # Create all tables defined in models
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup: drop all tables
    Base.metadata.drop_all(engine)
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
