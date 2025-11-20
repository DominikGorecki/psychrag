"""
Main CLI entry point for PsychRAG.

Usage:
    python -m psychrag.cli.drcli <command> [options]

Commands:
    dbinit              Initialize the database
    conv2md <file>      Convert PDF/EPUB to Markdown
    bib2db <file>       Extract bibliography and save to database
"""

import argparse
import sys
from pathlib import Path

# Configuration
OUTPUT_DIR = Path("output/markdown")


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="drcli",
        description="PsychRAG CLI tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # dbinit command
    subparsers.add_parser("dbinit", help="Initialize the database")

    # conv2md command
    conv_parser = subparsers.add_parser("conv2md", help="Convert PDF/EPUB to Markdown")
    conv_parser.add_argument("input_file", type=str, help="Input PDF or EPUB file")

    # bib2db command
    bib_parser = subparsers.add_parser("bib2db", help="Extract bibliography and save to database")
    bib_parser.add_argument("input_file", type=str, help="Input Markdown file")
    bib_parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview extracted metadata without saving to database"
    )
    bib_parser.add_argument(
        "--chars",
        type=int,
        default=None,
        help="Number of characters to extract from the beginning for metadata extraction"
    )
    bib_parser.add_argument(
        "--lines",
        type=int,
        default=None,
        help="Number of lines to extract from the beginning (overrides --chars)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "dbinit":
            from .db_commands import run_dbinit
            return run_dbinit(verbose=args.verbose)

        elif args.command == "conv2md":
            from .conv_commands import run_conv2md
            return run_conv2md(args.input_file, OUTPUT_DIR, verbose=args.verbose)

        elif args.command == "bib2db":
            from .bib_commands import run_bib2db
            return run_bib2db(args.input_file, verbose=args.verbose, preview=args.preview, chars=args.chars, lines=args.lines)

        else:
            parser.print_help()
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
