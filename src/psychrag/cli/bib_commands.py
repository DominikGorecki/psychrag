"""Bibliography extraction CLI commands."""

from pathlib import Path

from psychrag.chunking.bib_extractor import extract_metadata, EXTRACT_CHARS
from psychrag.data.database import SessionLocal
from psychrag.data.models import Work
from psychrag.utils import compute_file_hash


def run_bib2db(input_file: str, verbose: bool = False, preview: bool = False, chars: int | None = None, lines: int | None = None) -> int:
    """
    Extract bibliography and TOC from a markdown file and save to database.

    Args:
        input_file: Path to the input Markdown file.
        verbose: If True, print progress information.
        preview: If True, preview extracted text without saving to database.
        chars: Number of characters to extract for metadata extraction (None for default).
        lines: Number of lines to extract (overrides chars if specified).

    Returns:
        Exit code (0 for success, 1 for error).
    """
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return 1

    if input_path.suffix.lower() != ".md":
        print(f"Error: Expected Markdown file (.md), got: {input_path.suffix}")
        return 1

    try:
        # Compute hash
        content_hash = compute_file_hash(input_path)
        if verbose:
            print(f"File hash: {content_hash}")

        # Check if already processed
        with SessionLocal() as session:
            existing = session.query(Work).filter(Work.content_hash == content_hash).first()
            if existing:
                print(f"Already processed: {existing.title} (id={existing.id})")
                return 0

        # Read markdown content
        markdown_text = input_path.read_text(encoding="utf-8")

        # Determine text sample based on lines or chars
        if lines is not None:
            text_lines = markdown_text.split('\n')
            text_sample = '\n'.join(text_lines[:lines])
            extract_desc = f"{lines} lines"
            total_units = len(text_lines)
            unit_name = "lines"
        else:
            char_limit = chars if chars is not None else EXTRACT_CHARS
            text_sample = markdown_text[:char_limit]
            extract_desc = f"{char_limit} characters"
            total_units = len(markdown_text)
            unit_name = "characters"

        # Preview mode: show text that would be sent to LLM
        if preview:
            print(f"Preview of first {extract_desc} from {input_path.name}:")
            print("=" * 60)
            print(text_sample)
            print("=" * 60)
            if lines is not None:
                print(f"\nTotal lines shown: {min(len(text_lines), lines)}")
            else:
                print(f"\nTotal characters shown: {min(len(markdown_text), char_limit)}")
            print(f"Total file length: {total_units} {unit_name}")
            return 0

        # Extract metadata
        if verbose:
            print("Extracting metadata...")
        metadata = extract_metadata(markdown_text, chars=chars, lines=lines)

        # Parse year from publication_date
        year = None
        if metadata.bibliographic.publication_date:
            try:
                year = int(metadata.bibliographic.publication_date[:4])
            except (ValueError, TypeError):
                pass

        # Convert TOC entries to JSON-serializable format
        toc_json = [
            {"level": entry.level, "title": entry.title}
            for entry in metadata.toc.entries
        ]

        # Display extracted metadata
        print("\n=== Extracted Metadata ===")
        print(f"Title: {metadata.bibliographic.title or input_path.stem}")
        print(f"Authors: {', '.join(metadata.bibliographic.authors) if metadata.bibliographic.authors else 'N/A'}")
        print(f"Year: {year or 'N/A'}")
        print(f"Publisher: {metadata.bibliographic.publisher or 'N/A'}")
        print(f"ISBN: {metadata.bibliographic.isbn or 'N/A'}")
        print(f"Edition: {metadata.bibliographic.edition or 'N/A'}")
        print(f"\n=== Table of Contents ({len(toc_json)} entries) ===")
        for entry in toc_json[:20]:  # Show first 20 entries
            indent = "  " * (entry["level"] - 1)
            print(f"{indent}{entry['title']}")
        if len(toc_json) > 20:
            print(f"  ... and {len(toc_json) - 20} more entries")

        # Create Work object
        work = Work(
            title=metadata.bibliographic.title or input_path.stem,
            authors=", ".join(metadata.bibliographic.authors) if metadata.bibliographic.authors else None,
            year=year,
            publisher=metadata.bibliographic.publisher,
            isbn=metadata.bibliographic.isbn,
            markdown_path=str(input_path.absolute()),
            toc=toc_json,
            content_hash=content_hash,
        )

        # Save to database
        with SessionLocal() as session:
            session.add(work)
            session.commit()
            work_id = work.id

        print(f"Saved: {work.title} (id={work_id})")
        return 0

    except Exception as e:
        print(f"Extraction failed: {e}")
        return 1
