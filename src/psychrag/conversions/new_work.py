"""
Module for creating new work entries in the database.

This module provides functionality to insert bibliographic metadata
for psychology literature into the works table.

Example:
    from psychrag.sanitization.new_work import create_new_work
    from pathlib import Path

    work = create_new_work(
        title="Cognitive Psychology",
        markdown_path=Path("output/cognitive.md"),
        authors="John Smith",
        year=2025,
        publisher="Academic Press",
        isbn="978-0123456789",
        edition="3rd Edition"
    )
    print(f"Created work with ID: {work.id}")
"""

from pathlib import Path
from typing import Optional

from psychrag.data.database import get_session
from psychrag.data.models.work import Work
from psychrag.utils.file_utils import compute_file_hash
from psychrag.sanitization.toc_titles2toc import parse_toc_titles


class DuplicateWorkError(Exception):
    """Raised when a work with the same content hash already exists."""
    pass


def create_new_work(
    title: str,
    markdown_path: Path,
    authors: Optional[str] = None,
    year: Optional[int] = None,
    publisher: Optional[str] = None,
    isbn: Optional[str] = None,
    edition: Optional[str] = None,
    check_duplicates: bool = True,
    verbose: bool = False
) -> Work:
    """
    Create a new work entry in the database.

    Args:
        title: Title of the work (required).
        markdown_path: Path to the markdown file (required).
        authors: Author(s) of the work (optional).
        year: Year of publication (optional).
        publisher: Publisher name (optional).
        isbn: ISBN for books (optional).
        edition: Edition information (optional, stored in abstract field).
        check_duplicates: If True, check for duplicate content_hash (default: True).
        verbose: If True, print warning messages for TOC issues (default: False).

    Returns:
        The created Work object with ID populated.

    Raises:
        FileNotFoundError: If the markdown file does not exist.
        DuplicateWorkError: If a work with the same content hash already exists.
        ValueError: If validation fails.
    """
    # Validate markdown file exists
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    if not markdown_path.is_file():
        raise ValueError(f"Path is not a file: {markdown_path}")

    # Validate year if provided
    if year is not None:
        if not isinstance(year, int):
            raise ValueError(f"Year must be an integer, got: {type(year).__name__}")
        if year < 1000 or year > 9999:
            raise ValueError(f"Year must be a 4-digit year, got: {year}")

    # Compute content hash
    content_hash = compute_file_hash(markdown_path)

    # Check for TOC file and parse if present
    toc_path = markdown_path.parent / f"{markdown_path.stem}.toc_titles.md"
    toc_data = None

    if toc_path.exists():
        try:
            toc_result = parse_toc_titles(toc_path)
            # Convert to list of dicts for JSON storage
            toc_data = [{"level": entry.level, "title": entry.title} for entry in toc_result.entries]
        except Exception as e:
            if verbose:
                print(f"Warning: Could not parse TOC file {toc_path}: {e}")
    else:
        if verbose:
            print(f"Warning: TOC file not found: {toc_path}")

    # Check for duplicates if requested
    if check_duplicates:
        with get_session() as session:
            existing_work = session.query(Work).filter(
                Work.content_hash == content_hash
            ).first()

            if existing_work:
                raise DuplicateWorkError(
                    f"A work with the same content already exists (ID: {existing_work.id}, "
                    f"Title: '{existing_work.title}')"
                )

    # Create the work
    work = Work(
        title=title,
        markdown_path=str(markdown_path),
        authors=authors,
        year=year,
        publisher=publisher,
        isbn=isbn,
        abstract=edition,  # Store edition in abstract field as per your instruction
        content_hash=content_hash,
        toc=toc_data
    )

    # Insert into database
    with get_session() as session:
        session.add(work)
        session.commit()
        session.refresh(work)  # Refresh to get the generated ID

    return work
