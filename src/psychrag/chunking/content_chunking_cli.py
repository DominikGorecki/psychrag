#!/usr/bin/env python
"""CLI for content-aware chunking.

Usage:
    python -m psychrag.chunking.content_chunking_cli <work_id> [--verbose]

Examples:
    python -m psychrag.chunking.content_chunking_cli 1
    python -m psychrag.chunking.content_chunking_cli 1 --verbose
"""

import argparse
import sys

from psychrag.chunking.content_chunking import chunk_content


def main():
    """Main entry point for content chunking CLI."""
    parser = argparse.ArgumentParser(
        description="Create content-aware chunks from a work's sanitized markdown"
    )
    parser.add_argument(
        "work_id",
        type=int,
        help="ID of the work in the database"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed progress information"
    )

    args = parser.parse_args()

    try:
        count = chunk_content(args.work_id, verbose=args.verbose)
        print(f"Successfully created {count} content chunks for work {args.work_id}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
