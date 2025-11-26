"""
Database initialization script.

Database configuration (host, port, users) loaded from psychrag.config.json.
Passwords (secrets) loaded from .env file.

Example (as script):
    venv\\Scripts\\python -m psychrag.data.init_db

Example (as library):
    from psychrag.data.init_db import init_database
    init_database()
"""

import argparse
import sys
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

from psychrag.config import load_config
from .database import Base, engine, get_admin_database_url

# Import all models to register them with Base
from .models import Chunk, Query, Result, Work  # noqa: F401
from .models.io_file import IOFile  # noqa: F401


def create_database_and_user(verbose: bool = False) -> None:
    """
    Create the database and application user if they don't exist.

    Args:
        verbose: If True, print progress information.
    """
    load_dotenv()

    # Load config from JSON
    db_config = load_config().database

    db_name = db_config.db_name
    app_user = db_config.app_user
    app_password = os.getenv("POSTGRES_APP_PASSWORD", "psych_rag_secure_password")

    admin_url = get_admin_database_url()
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as conn:
        # Check if database exists
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
            {"db_name": db_name}
        )
        db_exists = result.fetchone() is not None

        if not db_exists:
            if verbose:
                print(f"Creating database: {db_name}")
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        else:
            if verbose:
                print(f"Database already exists: {db_name}")

        # Check if user exists
        result = conn.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = :username"),
            {"username": app_user}
        )
        user_exists = result.fetchone() is not None

        if not user_exists:
            if verbose:
                print(f"Creating user: {app_user}")
            # Password must be escaped as a literal since CREATE USER doesn't support parameters
            escaped_password = app_password.replace("'", "''")
            conn.execute(
                text(f"CREATE USER \"{app_user}\" WITH PASSWORD '{escaped_password}'")
            )
        else:
            if verbose:
                print(f"User already exists: {app_user}")

    # Grant privileges (connect to the specific database)
    db_url = (
        f"postgresql+psycopg://{db_config.admin_user}:"
        f"{os.getenv('POSTGRES_ADMIN_PASSWORD', 'postgres')}"
        f"@{db_config.host}:"
        f"{db_config.port}/{db_name}"
    )
    db_engine = create_engine(db_url, isolation_level="AUTOCOMMIT")

    with db_engine.connect() as conn:
        if verbose:
            print(f"Granting privileges to {app_user} on {db_name}")

        # Grant all privileges on database
        conn.execute(text(f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO "{app_user}"'))

        # Grant schema privileges
        conn.execute(text(f'GRANT ALL ON SCHEMA public TO "{app_user}"'))

        # Grant privileges on all tables (current and future)
        conn.execute(
            text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{app_user}"')
        )
        conn.execute(
            text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{app_user}"')
        )


def enable_pgvector_extension(verbose: bool = False) -> None:
    """
    Enable the pgvector extension in the database.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Enabling pgvector extension...")

    # Need admin privileges to create extensions
    db_config = load_config().database
    db_name = db_config.db_name
    db_url = (
        f"postgresql+psycopg://{db_config.admin_user}:"
        f"{os.getenv('POSTGRES_ADMIN_PASSWORD', 'postgres')}"
        f"@{db_config.host}:"
        f"{db_config.port}/{db_name}"
    )
    admin_engine = create_engine(db_url, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    if verbose:
        print("pgvector extension enabled")


def create_tables(verbose: bool = False) -> None:
    """
    Create all tables defined in the models.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating tables...")

    Base.metadata.create_all(bind=engine)

    if verbose:
        print("Tables created successfully")


def create_vector_indexes(verbose: bool = False) -> None:
    """
    Create HNSW indexes for vector columns.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating vector indexes...")

    with engine.connect() as conn:
        # Create HNSW index for cosine similarity on chunks.embedding
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw
            ON chunks USING hnsw (embedding vector_cosine_ops)
        """))

        # Create HNSW indexes for queries table embeddings
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_queries_embedding_original_hnsw
            ON queries USING hnsw (embedding_original vector_cosine_ops)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_queries_embedding_hyde_hnsw
            ON queries USING hnsw (embedding_hyde vector_cosine_ops)
        """))
        conn.commit()

    if verbose:
        print("Vector indexes created successfully")


def create_fulltext_search(verbose: bool = False) -> None:
    """
    Create full-text search infrastructure for chunks.

    This adds tsvector column, GIN index, and auto-update trigger.

    Args:
        verbose: If True, print progress information.
    """
    if verbose:
        print("Creating full-text search infrastructure...")

    with engine.connect() as conn:
        # Add tsvector column
        conn.execute(text("""
            ALTER TABLE chunks ADD COLUMN IF NOT EXISTS content_tsvector tsvector
        """))

        # Create GIN index for full-text search
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_chunks_content_tsvector_gin
            ON chunks USING gin (content_tsvector)
        """))

        # Create trigger function
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION chunks_content_tsvector_trigger()
            RETURNS trigger AS $$
            BEGIN
                NEW.content_tsvector := to_tsvector('english', COALESCE(NEW.content, ''));
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))

        # Create trigger (drop first to avoid duplicates)
        conn.execute(text("DROP TRIGGER IF EXISTS tsvector_update ON chunks"))
        conn.execute(text("""
            CREATE TRIGGER tsvector_update
            BEFORE INSERT OR UPDATE OF content ON chunks
            FOR EACH ROW
            EXECUTE FUNCTION chunks_content_tsvector_trigger()
        """))

        conn.commit()

    if verbose:
        print("Full-text search infrastructure created successfully")


def init_database(verbose: bool = False) -> None:
    """
    Initialize the database: create database, user, tables, and indexes.

    Args:
        verbose: If True, print progress information.
    """
    create_database_and_user(verbose=verbose)
    enable_pgvector_extension(verbose=verbose)
    create_tables(verbose=verbose)
    create_vector_indexes(verbose=verbose)
    create_fulltext_search(verbose=verbose)

    if verbose:
        print("Database initialization complete")


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Initialize PsychRAG database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              # Initialize database
  %(prog)s -v           # Verbose output
        """
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    try:
        init_database(verbose=args.verbose)
        return 0
    except Exception as e:
        print(f"Database initialization failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
