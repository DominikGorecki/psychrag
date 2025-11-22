"""Content-aware chunking for vector embeddings.

This module creates paragraph-level chunks from sanitized markdown documents,
using content-aware strategies including:
- Paragraph chunks with sentence overlap
- Heading hierarchy breadcrumbs
- Special handling for tables and figures

Usage:
    from psychrag.chunking.content_chunking import chunk_content
    count = chunk_content(work_id=1, verbose=True)

Examples:
    # Chunk all content for work ID 1
    from psychrag.chunking.content_chunking import chunk_content
    num_chunks = chunk_content(1)
    print(f"Created {num_chunks} chunks")
"""

import re
from pathlib import Path
from typing import Optional

import spacy

from psychrag.data.database import get_session
from psychrag.data.models import Chunk, Work
from psychrag.utils import compute_file_hash


# Load spaCy model for sentence tokenization
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise ImportError(
        "spaCy model 'en_core_web_sm' not found. "
        "Install with: python -m spacy download en_core_web_sm"
    )

# Chunking constants
TARGET_WORDS = 200
MAX_WORDS = 300
MIN_OVERLAP_SENTENCES = 2
MAX_OVERLAP_SENTENCES = 3
PARAGRAPH_BREAK_OVERLAP = 3


def _count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def _get_sentences(text: str) -> list[str]:
    """Split text into sentences using spaCy."""
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def _convert_bullets_to_sentences(text: str) -> str:
    """Convert bullet lists to flowing sentences.

    Args:
        text: Text potentially containing bullet lists.

    Returns:
        Text with bullets converted to sentences.
    """
    lines = text.split('\n')
    result_lines = []
    bullet_buffer = []

    def flush_bullets():
        if bullet_buffer:
            # Join bullets into sentences
            sentences = []
            for bullet in bullet_buffer:
                # Remove bullet marker and clean
                cleaned = re.sub(r'^[\s]*[-*+]\s*', '', bullet).strip()
                if cleaned:
                    # Ensure it ends with punctuation
                    if not cleaned[-1] in '.!?':
                        cleaned += '.'
                    sentences.append(cleaned)
            if sentences:
                result_lines.append(' '.join(sentences))
            bullet_buffer.clear()

    for line in lines:
        # Check if line is a bullet
        if re.match(r'^[\s]*[-*+]\s+', line):
            bullet_buffer.append(line)
        else:
            flush_bullets()
            result_lines.append(line)

    flush_bullets()
    return '\n'.join(result_lines)


def _parse_markdown_structure(content: str) -> dict:
    """Parse markdown into structured elements.

    Returns:
        Dictionary with:
        - headings: list of (line_num, level, text)
        - paragraphs: list of (start_line, end_line, text)
        - tables: list of (start_line, end_line, text)
        - figures: list of (line_num, text)
    """
    lines = content.splitlines()

    headings = []
    paragraphs = []
    tables = []
    figures = []

    i = 0
    while i < len(lines):
        line = lines[i]
        line_num = i + 1  # 1-indexed

        # Check for heading
        heading_match = re.match(r'^(#+)\s+(.*)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            if level <= 5:
                headings.append((line_num, level, line))
            i += 1
            continue

        # Check for figure (image)
        if re.match(r'^!\[.*\]\(.*\)', line):
            figures.append((line_num, line))
            i += 1
            continue

        # Check for table (starts with |)
        if line.strip().startswith('|'):
            table_start = line_num
            table_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            table_end = table_start + len(table_lines) - 1
            tables.append((table_start, table_end, '\n'.join(table_lines)))
            continue

        # Check for paragraph (non-empty, non-special line)
        if line.strip():
            para_start = line_num
            para_lines = [line]
            i += 1
            # Continue until blank line or special element
            while i < len(lines):
                next_line = lines[i]
                # Stop at blank line
                if not next_line.strip():
                    break
                # Stop at heading
                if re.match(r'^#+\s+', next_line):
                    break
                # Stop at figure
                if re.match(r'^!\[.*\]\(.*\)', next_line):
                    break
                # Stop at table
                if next_line.strip().startswith('|'):
                    break
                para_lines.append(next_line)
                i += 1

            para_end = para_start + len(para_lines) - 1
            para_text = '\n'.join(para_lines)
            # Convert bullets to sentences
            para_text = _convert_bullets_to_sentences(para_text)
            paragraphs.append((para_start, para_end, para_text))
            continue

        i += 1

    return {
        'headings': headings,
        'paragraphs': paragraphs,
        'tables': tables,
        'figures': figures
    }


def _build_heading_hierarchy(headings: list[tuple[int, int, str]]) -> dict[int, list[str]]:
    """Build heading hierarchy for each line number.

    Args:
        headings: List of (line_num, level, text).

    Returns:
        Dictionary mapping line numbers to heading hierarchy [H1, H2, H3].
    """
    hierarchy = {}
    current_stack = {}  # level -> heading text

    for line_num, level, text in headings:
        # Extract just the heading text (remove # marks)
        heading_text = re.sub(r'^#+\s+', '', text).strip()

        # Clear deeper levels
        for lvl in list(current_stack.keys()):
            if lvl >= level:
                del current_stack[lvl]

        # Set current level
        current_stack[level] = heading_text

        # Build breadcrumb
        breadcrumb = []
        for lvl in sorted(current_stack.keys()):
            breadcrumb.append(current_stack[lvl])

        hierarchy[line_num] = breadcrumb

    return hierarchy


def _find_heading_for_line(
    line_num: int,
    headings: list[tuple[int, int, str]],
    heading_hierarchy: dict[int, list[str]]
) -> tuple[Optional[int], list[str], int]:
    """Find the heading that contains a given line.

    Args:
        line_num: Line number to find heading for.
        headings: List of (line_num, level, text).
        heading_hierarchy: Dictionary mapping heading line numbers to breadcrumbs.

    Returns:
        Tuple of (heading_line_num, breadcrumb_list, level).
    """
    best_heading = None
    best_breadcrumb = []
    best_level = 0

    for h_line, h_level, _ in headings:
        if h_line < line_num:
            best_heading = h_line
            best_breadcrumb = heading_hierarchy.get(h_line, [])
            best_level = h_level
        else:
            break

    return best_heading, best_breadcrumb, best_level


def _format_breadcrumb(breadcrumb: list[str]) -> str:
    """Format heading breadcrumb for chunk content."""
    if not breadcrumb:
        return ""
    return ' > '.join(breadcrumb)


def _create_paragraph_chunks(
    paragraphs: list[tuple[int, int, str]],
    headings: list[tuple[int, int, str]],
    heading_hierarchy: dict[int, list[str]]
) -> list[dict]:
    """Create chunks from paragraphs with overlap strategy.

    Returns:
        List of chunk dictionaries with keys:
        - content: Full chunk text with breadcrumb
        - start_line: Paragraph start line
        - end_line: Paragraph end line
        - heading_line: Line number of heading (for parent lookup)
        - level: Heading level (e.g., 2 for H2)
        - vector_status: 'to_vec'
    """
    chunks = []

    # Group paragraphs by their heading
    heading_groups = {}
    for para_start, para_end, para_text in paragraphs:
        h_line, breadcrumb, level = _find_heading_for_line(para_start, headings, heading_hierarchy)

        if h_line not in heading_groups:
            heading_groups[h_line] = {
                'breadcrumb': breadcrumb,
                'level': level,
                'paragraphs': []
            }
        heading_groups[h_line]['paragraphs'].append((para_start, para_end, para_text))

    # Process each heading group
    for h_line, group in heading_groups.items():
        breadcrumb = group['breadcrumb']
        level = group['level']
        paras = group['paragraphs']

        breadcrumb_text = _format_breadcrumb(breadcrumb)
        breadcrumb_words = _count_words(breadcrumb_text) if breadcrumb_text else 0

        # Track overlap sentences for next chunk
        overlap_sentences = []
        is_first_in_heading = True

        for para_idx, (para_start, para_end, para_text) in enumerate(paras):
            sentences = _get_sentences(para_text)
            if not sentences:
                continue

            # Calculate available words for content
            available_words = MAX_WORDS - breadcrumb_words

            # Check if paragraph fits in one chunk
            para_words = _count_words(para_text)

            if para_words <= available_words:
                # Paragraph fits - check if we should combine with previous overlap
                chunk_sentences = []

                # Add overlap from previous chunk (if not first in heading)
                if not is_first_in_heading and overlap_sentences:
                    chunk_sentences.extend(overlap_sentences)

                chunk_sentences.extend(sentences)
                chunk_text = ' '.join(chunk_sentences)

                # Check total words
                total_words = _count_words(chunk_text) + breadcrumb_words

                if total_words <= MAX_WORDS:
                    # Create chunk
                    content = f"{breadcrumb_text}\n{chunk_text}" if breadcrumb_text else chunk_text
                    chunks.append({
                        'content': content,
                        'start_line': para_start,
                        'end_line': para_end,
                        'heading_line': h_line,
                        'level': level,
                        'vector_status': 'to_vec'
                    })

                    # Set overlap for next chunk
                    overlap_sentences = sentences[-MAX_OVERLAP_SENTENCES:] if len(sentences) >= MIN_OVERLAP_SENTENCES else sentences
                else:
                    # Too big with overlap - create without overlap
                    content = f"{breadcrumb_text}\n{para_text}" if breadcrumb_text else para_text
                    chunks.append({
                        'content': content,
                        'start_line': para_start,
                        'end_line': para_end,
                        'heading_line': h_line,
                        'level': level,
                        'vector_status': 'to_vec'
                    })
                    overlap_sentences = sentences[-MAX_OVERLAP_SENTENCES:] if len(sentences) >= MIN_OVERLAP_SENTENCES else sentences
            else:
                # Paragraph too long - need to split
                current_chunk_sentences = []

                # Add overlap from previous (if not first)
                if not is_first_in_heading and overlap_sentences:
                    current_chunk_sentences.extend(overlap_sentences)

                for sent in sentences:
                    test_sentences = current_chunk_sentences + [sent]
                    test_text = ' '.join(test_sentences)
                    test_words = _count_words(test_text) + breadcrumb_words

                    if test_words <= MAX_WORDS:
                        current_chunk_sentences.append(sent)
                    else:
                        # Flush current chunk
                        if current_chunk_sentences:
                            chunk_text = ' '.join(current_chunk_sentences)
                            content = f"{breadcrumb_text}\n{chunk_text}" if breadcrumb_text else chunk_text
                            chunks.append({
                                'content': content,
                                'start_line': para_start,
                                'end_line': para_end,
                                'heading_line': h_line,
                                'level': level,
                                'vector_status': 'to_vec'
                            })

                            # Overlap for next chunk within same paragraph
                            overlap_count = min(PARAGRAPH_BREAK_OVERLAP, len(current_chunk_sentences))
                            current_chunk_sentences = current_chunk_sentences[-overlap_count:] + [sent]
                        else:
                            # Single sentence too long - just add it
                            current_chunk_sentences = [sent]

                # Final chunk from paragraph
                if current_chunk_sentences:
                    chunk_text = ' '.join(current_chunk_sentences)
                    content = f"{breadcrumb_text}\n{chunk_text}" if breadcrumb_text else chunk_text
                    chunks.append({
                        'content': content,
                        'start_line': para_start,
                        'end_line': para_end,
                        'heading_line': h_line,
                        'level': level,
                        'vector_status': 'to_vec'
                    })
                    overlap_sentences = current_chunk_sentences[-MAX_OVERLAP_SENTENCES:] if len(current_chunk_sentences) >= MIN_OVERLAP_SENTENCES else current_chunk_sentences

            is_first_in_heading = False

    return chunks


def _create_table_chunks(
    tables: list[tuple[int, int, str]],
    headings: list[tuple[int, int, str]],
    heading_hierarchy: dict[int, list[str]]
) -> list[dict]:
    """Create chunks for tables."""
    chunks = []

    for table_start, table_end, table_text in tables:
        h_line, breadcrumb, level = _find_heading_for_line(table_start, headings, heading_hierarchy)
        breadcrumb_text = _format_breadcrumb(breadcrumb)

        content = f"{breadcrumb_text}\n{table_text}" if breadcrumb_text else table_text

        chunks.append({
            'content': content,
            'start_line': table_start,
            'end_line': table_end,
            'heading_line': h_line,
            'level': level,
            'vector_status': 'tbl'
        })

    return chunks


def _create_figure_chunks(
    figures: list[tuple[int, str]],
    headings: list[tuple[int, int, str]],
    heading_hierarchy: dict[int, list[str]]
) -> list[dict]:
    """Create chunks for figures."""
    chunks = []

    for fig_line, fig_text in figures:
        h_line, breadcrumb, level = _find_heading_for_line(fig_line, headings, heading_hierarchy)
        breadcrumb_text = _format_breadcrumb(breadcrumb)

        content = f"{breadcrumb_text}\n{fig_text}" if breadcrumb_text else fig_text

        chunks.append({
            'content': content,
            'start_line': fig_line,
            'end_line': fig_line,
            'heading_line': h_line,
            'level': level,
            'vector_status': 'fig'
        })

    return chunks


def chunk_content(work_id: int, verbose: bool = False) -> int:
    """Chunk content from a work into the database.

    Args:
        work_id: ID of the work in the database.
        verbose: Whether to print progress information.

    Returns:
        Number of chunks created.

    Raises:
        ValueError: If work not found or files missing.
    """
    with get_session() as session:
        # Get work and validate
        work = session.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work with ID {work_id} not found")

        if not work.markdown_path:
            raise ValueError(f"Work {work_id} has no markdown_path")

        markdown_path = Path(work.markdown_path)
        if not markdown_path.exists():
            raise ValueError(f"Markdown file not found: {markdown_path}")

        # Verify it's a sanitized file
        if not markdown_path.name.endswith('.sanitized.md'):
            raise ValueError(f"Expected sanitized markdown file (*.sanitized.md), got: {markdown_path.name}")

        # Verify content hash (use file-based hash to match how it was stored)
        content_hash = compute_file_hash(markdown_path)

        if work.content_hash and work.content_hash != content_hash:
            raise ValueError(
                f"Content hash mismatch for work {work_id}. "
                f"Expected: {work.content_hash}, Got: {content_hash}"
            )

        # Read content for parsing
        content = markdown_path.read_text(encoding='utf-8')

        if verbose:
            print(f"Processing work {work_id}: {work.title}")
            print(f"Markdown: {markdown_path}")

        # Parse markdown structure
        structure = _parse_markdown_structure(content)
        headings = structure['headings']
        heading_hierarchy = _build_heading_hierarchy(headings)

        if verbose:
            print(f"Found {len(headings)} headings, {len(structure['paragraphs'])} paragraphs, "
                  f"{len(structure['tables'])} tables, {len(structure['figures'])} figures")

        # Create chunks
        all_chunks = []

        # Paragraph chunks
        para_chunks = _create_paragraph_chunks(
            structure['paragraphs'], headings, heading_hierarchy
        )
        all_chunks.extend(para_chunks)

        # Table chunks
        table_chunks = _create_table_chunks(
            structure['tables'], headings, heading_hierarchy
        )
        all_chunks.extend(table_chunks)

        # Figure chunks
        figure_chunks = _create_figure_chunks(
            structure['figures'], headings, heading_hierarchy
        )
        all_chunks.extend(figure_chunks)

        if verbose:
            print(f"Created {len(para_chunks)} paragraph chunks, "
                  f"{len(table_chunks)} table chunks, {len(figure_chunks)} figure chunks")

        # Get existing heading chunks for parent lookup
        heading_chunks = session.query(Chunk).filter(
            Chunk.work_id == work_id,
            Chunk.level.in_(['H1', 'H2', 'H3', 'H4', 'H5'])
        ).all()

        # Map start_line to chunk id
        heading_chunk_map = {chunk.start_line: chunk.id for chunk in heading_chunks}

        # Save chunks to database
        chunks_created = 0
        missing_parents = 0

        for chunk_data in all_chunks:
            # Find parent_id
            parent_id = None
            heading_line = chunk_data.get('heading_line')

            if heading_line:
                parent_id = heading_chunk_map.get(heading_line)
                if parent_id is None:
                    missing_parents += 1
                    if verbose:
                        print(f"  Warning: No parent chunk found for heading at line {heading_line}")

            # Create chunk
            level = chunk_data['level']
            level_str = f"H{level}-chunk" if level else "chunk"

            chunk = Chunk(
                parent_id=parent_id,
                work_id=work_id,
                level=level_str,
                content=chunk_data['content'],
                embedding=None,
                start_line=chunk_data['start_line'],
                end_line=chunk_data['end_line'],
                vector_status=chunk_data['vector_status']
            )

            session.add(chunk)
            chunks_created += 1

            if verbose and chunks_created <= 5:
                status = chunk_data['vector_status']
                print(f"  Created {level_str} chunk (lines {chunk_data['start_line']}-{chunk_data['end_line']}, {status})")

        if verbose and chunks_created > 5:
            print(f"  ... and {chunks_created - 5} more chunks")

        session.commit()

        if verbose:
            print(f"\nTotal: {chunks_created} chunks created for work {work_id}")
            if missing_parents:
                print(f"Warning: {missing_parents} chunks have no parent (heading chunk not found)")

        return chunks_created
