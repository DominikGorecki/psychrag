"""
CLI for applying title changes to markdown documents.

Usage:
    python -m psychrag.sanitization.apply_title_changes_cli <changes_file> <work_id>

Examples:
    python -m psychrag.sanitization.apply_title_changes_cli output/book.title_changes.md 1
"""

import argparse
import sys
from pathlib import Path

from .apply_title_changes import preview_title_changes, apply_title_changes


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Apply title changes to create a sanitized markdown file"
    )
    parser.add_argument(
        "changes_file",
        type=Path,
        help="Path to the .title_changes.md file"
    )
    parser.add_argument(
        "work_id",
        type=int,
        help="ID of the Work record in the database"
    )

    args = parser.parse_args()

    try:
        # Get preview
        previews = preview_title_changes(args.changes_file, args.work_id)

        if not previews:
            print("No changes to apply.")
            return 0

        # Display preview
        print(f"\n=== Preview of {len(previews)} changes ===\n")
        for preview in previews:
            print(f"## Line {preview['line_num']}")
            print(f"[Old] {preview['old_line']}")
            print(f"[New] {preview['new_line']}")
            print()

        # Prompt for confirmation
        print("Apply these changes? [Y/N]: ", end="")
        response = input().strip().upper()

        if response != "Y":
            print("Changes not applied.")
            return 0

        # Apply changes
        output_path = apply_title_changes(args.changes_file, args.work_id)
        print(f"\nSanitized file created: {output_path}")
        print("Database updated with new hash and path.")
        print("File set to read-only.")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
