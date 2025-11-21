"""Chunk document headings into database.

This module reads a sanitized markdown document and its vectorization suggestions,
then creates Chunk records in the database for all headings marked for vectorization.

Usage:
    from psychrag.chunking.chunk_headings import chunk_headings
    count = chunk_headings(work_id=1, verbose=True)

Examples:
    # Chunk all headings for work ID 1
    from psychrag.chunking.chunk_headings import chunk_headings
    num_chunks = chunk_headings(1)
    print(f"Created {num_chunks} chunks")
"""

import re
from pathlib import Path

from psychrag.data.database import get_session
from psychrag.data.models import Chunk, Work


def _parse_suggestions(suggestions_path: Path) -> dict[int, str]:
    """Parse vectorization suggestions file.

    Args:
        suggestions_path: Path to the .vectorize_suggestions.md file.

    Returns:
        Dictionary mapping line numbers to SKIP/VECTORIZE decisions.
    """
    content = suggestions_path.read_text(encoding='utf-8')
    decisions = {}

    # Extract from code block
    match = re.search(r'```\n(.*?)```', content, re.DOTALL)
    if not match:
        return decisions

    for line in match.group(1).strip().split('\n'):
        m = re.match(r'(\d+):\s*(SKIP|VECTORIZE)', line.strip(), re.IGNORECASE)
        if m:
            decisions[int(m.group(1))] = m.group(2).upper()

    return decisions


def _parse_headings(content: str) -> list[tuple[int, int, str]]:
    """Parse all headings from markdown content.

    Args:
        content: Markdown content.

    Returns:
        List of tuples (line_num, level, heading_text).
    """
    headings = []
    lines = content.splitlines()

    for i, line in enumerate(lines, start=1):
        match = re.match(r'^(#+)\s+(.*)$', line)
        if match:
            level = len(match.group(1))
            if level <= 5:  # Only H1-H5
                headings.append((i, level, line))

    return headings


def _calculate_heading_ranges(
    headings: list[tuple[int, int, str]],
    total_lines: int
) -> list[tuple[int, int, int, int]]:
    """Calculate start and end lines for each heading.

    Args:
        headings: List of (line_num, level, heading_text).
        total_lines: Total number of lines in the document.

    Returns:
        List of tuples (line_num, level, start_line, end_line).
    """
    ranges = []

    for i, (line_num, level, _) in enumerate(headings):
        start_line = line_num

        # Find end: next heading with same or higher level (lower number)
        end_line = total_lines
        for j in range(i + 1, len(headings)):
            next_line, next_level, _ = headings[j]
            if next_level <= level:
                end_line = next_line - 1
                break

        ranges.append((line_num, level, start_line, end_line))

    return ranges


def _get_content_for_range(lines: list[str], start: int, end: int) -> str:
    """Extract content for a line range.

    Args:
        lines: List of all lines (0-indexed).
        start: Start line number (1-indexed).
        end: End line number (1-indexed).

    Returns:
        Content string.
    """
    # Convert to 0-indexed
    return '\n'.join(lines[start - 1:end])


def chunk_headings(work_id: int, verbose: bool = False) -> int:
    """Chunk all headings from a work into the database.

    Args:
        work_id: ID of the work in the database.
        verbose: Whether to print progress information.

    Returns:
        Number of chunks created.

    Raises:
        ValueError: If work not found or files missing.
    """
    with get_session() as session:
        # Step 1: Get work and markdown path
        work = session.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work with ID {work_id} not found")

        if not work.markdown_path:
            raise ValueError(f"Work {work_id} has no markdown_path")

        markdown_path = Path(work.markdown_path)
        if not markdown_path.exists():
            raise ValueError(f"Markdown file not found: {markdown_path}")

        # Step 2: Determine suggestions file path
        suggestions_path = markdown_path.with_suffix('.vectorize_suggestions.md')
        if not suggestions_path.exists():
            raise ValueError(f"Suggestions file not found: {suggestions_path}")

        if verbose:
            print(f"Processing work {work_id}: {work.title}")
            print(f"Markdown: {markdown_path}")
            print(f"Suggestions: {suggestions_path}")

        # Step 3: Load and parse files
        content = markdown_path.read_text(encoding='utf-8')
        lines = content.splitlines()
        total_lines = len(lines)

        decisions = _parse_suggestions(suggestions_path)
        headings = _parse_headings(content)
        ranges = _calculate_heading_ranges(headings, total_lines)

        if verbose:
            print(f"Found {len(headings)} headings, {sum(1 for d in decisions.values() if d == 'VECTORIZE')} to vectorize")

        # Step 4: Filter to only VECTORIZE headings
        to_vectorize = [
            (line_num, level, start, end)
            for line_num, level, start, end in ranges
            if decisions.get(line_num) == 'VECTORIZE'
        ]

        # Step 5: Create chunks in order, tracking IDs by start_line
        chunk_id_map: dict[int, int] = {}  # start_line -> chunk.id
        chunks_created = 0

        # Sort by line number to process in document order
        to_vectorize.sort(key=lambda x: x[0])

        for line_num, level, start_line, end_line in to_vectorize:
            # Find parent_id
            parent_id = None
            if level > 1:
                # Find nearest heading above with lower level number
                for prev_line, prev_level, prev_start, _ in reversed(ranges):
                    if prev_start < start_line and prev_level < level:
                        # Check if this parent was vectorized
                        if prev_start in chunk_id_map:
                            parent_id = chunk_id_map[prev_start]
                        break

            # Get content
            chunk_content = _get_content_for_range(lines, start_line, end_line)

            # Create chunk
            chunk = Chunk(
                parent_id=parent_id,
                work_id=work_id,
                level=f"H{level}",
                content=chunk_content,
                embedding=None,
                start_line=start_line,
                end_line=end_line,
                vector_status="no_vec"
            )

            session.add(chunk)
            session.flush()  # Get the ID

            chunk_id_map[start_line] = chunk.id
            chunks_created += 1

            if verbose:
                parent_info = f", parent_id={parent_id}" if parent_id else ""
                print(f"  Created H{level} chunk (lines {start_line}-{end_line}){parent_info}")

        session.commit()

        if verbose:
            print(f"Created {chunks_created} chunks for work {work_id}")

        return chunks_created
