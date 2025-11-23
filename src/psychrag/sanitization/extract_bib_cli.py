"""
CLI for extracting bibliographic information from markdown files.

Usage:
    python -m psychrag.sanitization.extract_bib_cli document.md
    python -m psychrag.sanitization.extract_bib_cli document.md --chars 2000 -v
    python -m psychrag.sanitization.extract_bib_cli document.md --lines 100 -v
"""

import argparse
import sys
from pathlib import Path

from psychrag.sanitization.extract_bib import extract_bibliographic_info
from psychrag.data.database import SessionLocal
from psychrag.data.models import Work
from psychrag.utils import compute_file_hash


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Extract bibliographic information from markdown files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.md                    # Extract and prompt to save
  %(prog)s document.md --chars 2000       # Use more context
  %(prog)s document.md --lines 100        # Use first 100 lines
  %(prog)s document.md -v                 # Verbose output
        """
    )

    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input Markdown file"
    )

    parser.add_argument(
        "--chars",
        type=int,
        default=None,
        help="Number of characters to extract from the beginning for metadata extraction"
    )

    parser.add_argument(
        "--lines",
        type=int,
        default=None,
        help="Number of lines to extract from the beginning (overrides --chars)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    try:
        input_path = Path(args.input_file)

        if not input_path.exists():
            print(f"Error: File not found: {input_path}", file=sys.stderr)
            return 1

        # Compute hash
        content_hash = compute_file_hash(input_path)
        if args.verbose:
            print(f"File hash: {content_hash}")

        # Check if already processed
        with SessionLocal() as session:
            existing = session.query(Work).filter(Work.content_hash == content_hash).first()
            if existing:
                print(f"Already processed: {existing.title} (id={existing.id})")
                return 0

        # Extract bibliographic info
        if args.verbose:
            print("Extracting bibliographic information...")

        bib_info = extract_bibliographic_info(
            markdown_path=args.input_file,
            chars=args.chars,
            lines=args.lines,
        )

        # Parse year from publication_date
        year = None
        if bib_info.publication_date:
            try:
                year = int(bib_info.publication_date[:4])
            except (ValueError, TypeError):
                pass

        # Display extracted metadata
        print("\n=== Extracted Bibliographic Information ===")
        print(f"Title: {bib_info.title or input_path.stem}")
        print(f"Authors: {', '.join(bib_info.authors) if bib_info.authors else 'N/A'}")
        print(f"Year: {year or 'N/A'}")
        print(f"Publisher: {bib_info.publisher or 'N/A'}")
        print(f"ISBN: {bib_info.isbn or 'N/A'}")
        print(f"Edition: {bib_info.edition or 'N/A'}")

        # Prompt user to save
        print("\nSave to database? [Y/N]: ", end="")
        response = input().strip().upper()

        if response != "Y":
            print("Not saved.")
            return 0

        # Create Work object (without TOC - that comes later)
        work = Work(
            title=bib_info.title or input_path.stem,
            authors=", ".join(bib_info.authors) if bib_info.authors else None,
            year=year,
            publisher=bib_info.publisher,
            isbn=bib_info.isbn,
            markdown_path=str(input_path.absolute()),
            content_hash=content_hash,
        )

        # Save to database
        with SessionLocal() as session:
            session.add(work)
            session.commit()
            work_id = work.id

        print(f"Saved: {work.title} (id={work_id})")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
