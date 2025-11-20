"""Bibliography extraction CLI commands."""

import hashlib
from pathlib import Path

from psychrag.chunking.bib_extractor import extract_metadata
from psychrag.data.database import SessionLocal
from psychrag.data.models import Work


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal hash string.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def run_bib2db(input_file: str, verbose: bool = False) -> int:
    """
    Extract bibliography and TOC from a markdown file and save to database.

    Args:
        input_file: Path to the input Markdown file.
        verbose: If True, print progress information.

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

        # Extract metadata
        if verbose:
            print("Extracting metadata...")
        metadata = extract_metadata(markdown_text)

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
