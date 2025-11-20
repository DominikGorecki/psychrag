"""Database CLI commands."""

from psychrag.data.init_db import init_database


def run_dbinit(verbose: bool = False) -> int:
    """
    Initialize the database.

    Args:
        verbose: If True, print progress information.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        init_database(verbose=verbose)
        if verbose:
            print("Database initialized successfully")
        return 0
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return 1
