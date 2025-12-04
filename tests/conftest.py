"""Shared test fixtures for the test suite.

This module provides database fixtures and other shared test utilities.
"""

import pytest
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from psychrag.data.database import Base

# Import models to ensure they are registered with Base
from psychrag.data.models.prompt_template import PromptTemplate  # noqa: F401
from psychrag.data.models.prompt_meta import PromptMeta  # noqa: F401
from psychrag.data.models.work import Work  # noqa: F401
from psychrag.data.models.chunk import Chunk  # noqa: F401
from psychrag.data.models.io_file import IOFile  # noqa: F401
from psychrag.data.models.query import Query  # noqa: F401
from psychrag.data.models.result import Result  # noqa: F401

# Note: passive_deletes is now configured in the Chunk model itself
# This ensures database-level CASCADE deletes work correctly


@pytest.fixture(scope="function")
def engine():
    """Create in-memory SQLite engine for tests.

    Each test gets a fresh database. The engine is torn down after
    the test completes.

    Creates SQLite-compatible tables including Work and Chunk models.
    Vector types are handled by creating tables manually with BLOB instead.
    Foreign keys are enabled to support CASCADE deletes and constraint validation.

    Yields:
        SQLAlchemy Engine instance with compatible tables created.
    """
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")

    # Enable foreign keys for SQLite (required for CASCADE and FK constraints)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create Work table (no Vector type, so it works normally)
    Work.__table__.create(engine, checkfirst=True)
    
    # Create Chunk table manually with Vector replaced by BLOB
    # This is necessary because pgvector's Vector type doesn't work with SQLite
    with engine.connect() as conn:
        # Ensure foreign keys are enabled for this connection
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                work_id INTEGER NOT NULL,
                level VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                heading_breadcrumbs VARCHAR(500),
                embedding BLOB,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                vector_status VARCHAR(10) NOT NULL DEFAULT 'no_vec',
                FOREIGN KEY(parent_id) REFERENCES chunks (id) ON DELETE CASCADE,
                FOREIGN KEY(work_id) REFERENCES works (id) ON DELETE CASCADE
            )
        """))
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chunks_parent_id ON chunks(parent_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chunks_work_id ON chunks(work_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chunks_level ON chunks(level)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chunks_vector_status ON chunks(vector_status)"))
        conn.commit()
    
    PromptTemplate.__table__.create(engine, checkfirst=True)
    IOFile.__table__.create(engine, checkfirst=True)
    
    # Create PromptMeta table manually with JSONB replaced by TEXT
    # This is necessary because PostgreSQL's JSONB type doesn't work with SQLite
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prompt_meta (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                function_tag VARCHAR(100) NOT NULL UNIQUE,
                variables TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """))
        # Create index on function_tag
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_prompt_meta_function_tag ON prompt_meta(function_tag)"))
        conn.commit()
    
    # Create Query table manually with Vector replaced by BLOB
    # This is necessary because pgvector's Vector type doesn't work with SQLite
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                original_query TEXT NOT NULL,
                expanded_queries TEXT,
                hyde_answer TEXT,
                intent VARCHAR(50),
                entities TEXT,
                embedding_original BLOB,
                embeddings_mqe TEXT,
                embedding_hyde BLOB,
                vector_status VARCHAR(10) NOT NULL DEFAULT 'no_vec',
                retrieved_context TEXT,
                clean_retrieval_context TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_queries_intent ON queries(intent)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_queries_vector_status ON queries(vector_status)"))
        conn.commit()
    
    # Create Result table (no Vector type, so it works normally)
    Result.__table__.create(engine, checkfirst=True)

    yield engine

    # Cleanup: drop tables in reverse order (respecting foreign keys)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(text("DROP TABLE IF EXISTS results"))
        conn.execute(text("DROP TABLE IF EXISTS queries"))
        conn.execute(text("DROP TABLE IF EXISTS prompt_meta"))
        conn.execute(text("DROP TABLE IF EXISTS chunks"))
        conn.commit()
    Work.__table__.drop(engine, checkfirst=True)
    PromptTemplate.__table__.drop(engine, checkfirst=True)
    IOFile.__table__.drop(engine, checkfirst=True)
    engine.dispose()


@pytest.fixture(scope="function")
def session(engine) -> Session:
    """Create database session for tests with automatic rollback.

    Each test gets a fresh session connected to the test database.
    After the test completes, all changes are rolled back to ensure
    test isolation.

    Foreign keys are enabled for each session to ensure CASCADE deletes
    and foreign key constraint validation work correctly.

    Args:
        engine: The test database engine fixture.

    Yields:
        SQLAlchemy Session instance.
    """
    # Create a session factory bound to the test engine
    TestingSessionLocal = sessionmaker(bind=engine)

    # Create a new session for this test
    session = TestingSessionLocal()
    
    # Enable foreign keys for this session (SQLite requirement)
    session.execute(text("PRAGMA foreign_keys=ON"))
    session.commit()

    yield session

    # Cleanup: rollback any changes and close the session
    session.rollback()
    session.close()
