"""CLI for suggesting heading hierarchy changes.

Analyze markdown headings using AI and suggest corrections based on
the table of contents stored in the database.

Usage:
    venv\\Scripts\\python -m psychrag.sanitization.suggest_heading_changes_cli <titles_file>

Examples:
    # Suggest changes for a titles file (creates book.title_changes.md)
    venv\\Scripts\\python -m psychrag.sanitization.suggest_heading_changes_cli book.titles.md

Options:
    titles_file         Path to the .titles.md file created by extract_titles_cli
"""

import argparse
import sys
from pathlib import Path

from .suggest_heading_changes import suggest_heading_changes


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Suggest heading hierarchy changes using AI"
    )
    parser.add_argument(
        "titles_file",
        type=Path,
        help="Path to the .titles.md file to analyze"
    )

    args = parser.parse_args()

    try:
        output_path = suggest_heading_changes(args.titles_file)
        print(f"Heading changes saved to: {output_path}")
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
