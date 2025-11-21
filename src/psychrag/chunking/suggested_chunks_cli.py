"""CLI for suggesting which document sections to vectorize.

Usage:
    python -m psychrag.chunking.suggested_chunks_cli document.sanitized.md
    python -m psychrag.chunking.suggested_chunks_cli document.sanitized.md --bib-file bib.json -v
"""

import argparse
import json
import sys
from pathlib import Path

from psychrag.chunking.bib_extractor import BibliographicInfo
from psychrag.chunking.suggested_chunks import suggest_chunks


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Analyze document headings and suggest which sections to vectorize"
    )

    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the sanitized markdown file"
    )

    parser.add_argument(
        "--bib-file",
        type=Path,
        help="Path to JSON file with bibliographic information"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    # Load bibliographic info if provided
    bib_info = None
    if args.bib_file:
        if not args.bib_file.exists():
            print(f"Error: Bib file not found: {args.bib_file}", file=sys.stderr)
            return 1
        try:
            bib_data = json.loads(args.bib_file.read_text(encoding='utf-8'))
            bib_info = BibliographicInfo(**bib_data)
        except Exception as e:
            print(f"Error loading bib file: {e}", file=sys.stderr)
            return 1

    try:
        output_path = suggest_chunks(
            args.input_file,
            bib_info=bib_info,
            verbose=args.verbose
        )
        print(f"Suggestions saved to: {output_path}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
