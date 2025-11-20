"""CLI for extracting markdown titles from documents.

Extract all headings from a markdown file and save them with line numbers
for hierarchy analysis.

Usage:
    venv\\Scripts\\python -m psychrag.sanitization.extract_titles_cli <input_file> [options]

Examples:
    # Extract titles from a markdown file (creates book.titles.md)
    venv\\Scripts\\python -m psychrag.sanitization.extract_titles_cli book.md

    # Specify custom output path
    venv\\Scripts\\python -m psychrag.sanitization.extract_titles_cli book.md -o output/titles.md

Options:
    input_file          Path to the markdown file to analyze
    -o, --output        Optional output file path (default: <input>.titles.md)
"""

import argparse
import sys
from pathlib import Path

from .extract_titles import extract_titles_to_file


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Extract all titles from a markdown file"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the markdown file to analyze"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output file path (default: <input>.titles.md)"
    )

    args = parser.parse_args()

    try:
        output_path = extract_titles_to_file(args.input_file, args.output)
        print(f"Titles extracted to: {output_path}")
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
