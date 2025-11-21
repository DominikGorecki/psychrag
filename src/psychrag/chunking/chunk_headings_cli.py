"""CLI for chunking document headings into database.

Usage:
    python -m psychrag.chunking.chunk_headings_cli 1
    python -m psychrag.chunking.chunk_headings_cli 1 -v
"""

import argparse
import sys

from psychrag.chunking.chunk_headings import chunk_headings


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Chunk document headings into database"
    )

    parser.add_argument(
        "work_id",
        type=int,
        help="ID of the work in the database"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    try:
        count = chunk_headings(args.work_id, verbose=args.verbose)
        print(f"Successfully created {count} chunks for work {args.work_id}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
