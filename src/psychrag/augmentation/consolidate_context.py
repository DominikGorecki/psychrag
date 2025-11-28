"""
Context consolidation for clean retrieval results.

This module consolidates retrieved chunks by grouping them under parents
and merging adjacent chunks to create cleaner context for augmentation.

Usage:
    from psychrag.augmentation.consolidate_context import consolidate_context
    result = consolidate_context(query_id=1, verbose=True)
"""

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from psychrag.data.database import get_session
from psychrag.data.models import Chunk, Query, Work
from psychrag.utils.file_utils import compute_file_hash


@dataclass
class ConsolidatedGroup:
    """A consolidated group of chunks."""

    chunk_ids: list[int]
    parent_id: int | None
    work_id: int
    content: str
    start_line: int
    end_line: int
    score: float
    heading_chain: list[str] | None = None  # Breadcrumb trail of section headings


@dataclass
class ConsolidationResult:
    """Result of the consolidation operation."""

    query_id: int
    original_count: int
    consolidated_count: int
    groups: list[ConsolidatedGroup]


# Default parameters
DEFAULT_COVERAGE_THRESHOLD = 0.5
DEFAULT_LINE_GAP = 7


def _get_level_order(level: str) -> int:
    """Get numeric order for heading level (higher = deeper)."""
    level_map = {
        "H1": 1, "H2": 2, "H3": 3, "H4": 4, "H5": 5,
        "sentence": 6, "chunk": 7
    }
    return level_map.get(level, 10)


def _get_heading_chain(
    parent_id: int | None,
    parents_map: dict
) -> list[str]:
    """Walk up the parent tree to build heading breadcrumbs.

    Returns a list of heading texts from root (H1) to the immediate parent,
    providing hierarchical context for the chunk.

    Args:
        parent_id: The parent_id of the current chunk/group
        parents_map: Dict mapping chunk_id to Chunk objects

    Returns:
        List of heading texts, e.g., ["Chapter 5: Therapy", "Schema Therapy", "Core Techniques"]
    """
    chain = []
    current_id = parent_id

    while current_id and current_id in parents_map:
        parent = parents_map[current_id]

        # Extract heading text from first line of content
        content = parent.content or ""
        first_line = content.split('\n')[0].strip()

        # Remove markdown heading markers (# ## ### etc.)
        if first_line.startswith('#'):
            heading_text = first_line.lstrip('#').strip()
        else:
            heading_text = first_line

        # Only include non-empty headings
        if heading_text:
            chain.insert(0, heading_text)  # Insert at beginning (root first)

        # Move up to next parent
        current_id = parent.parent_id

    return chain


def _read_content_from_file(
    markdown_path: Path,
    start_line: int,
    end_line: int
) -> str:
    """Read content from markdown file by line range."""
    lines = markdown_path.read_text(encoding='utf-8').splitlines()
    # Convert to 0-indexed
    return '\n'.join(lines[start_line - 1:end_line])


def _calculate_coverage(
    items: list[dict],
    parent_start: int,
    parent_end: int
) -> float:
    """Calculate what percentage of parent is covered by items."""
    parent_lines = parent_end - parent_start + 1
    if parent_lines <= 0:
        return 0.0

    # Count covered lines
    covered = set()
    for item in items:
        for line in range(item['start_line'], item['end_line'] + 1):
            covered.add(line)

    # Only count lines within parent range
    covered_in_parent = covered & set(range(parent_start, parent_end + 1))
    return len(covered_in_parent) / parent_lines


def _merge_adjacent_items(
    items: list[dict],
    markdown_path: Path,
    line_gap: int = DEFAULT_LINE_GAP
) -> list[dict]:
    """Merge items that are within line_gap of each other."""
    if not items:
        return []

    # Sort by start_line
    sorted_items = sorted(items, key=lambda x: x['start_line'])

    merged = []
    current_group = [sorted_items[0]]

    for item in sorted_items[1:]:
        last = current_group[-1]
        # Check if within gap
        if item['start_line'] - last['end_line'] <= line_gap:
            current_group.append(item)
        else:
            # Finalize current group
            merged.append(_finalize_group(current_group, markdown_path))
            current_group = [item]

    # Finalize last group
    if current_group:
        merged.append(_finalize_group(current_group, markdown_path))

    return merged


def _finalize_group(
    items: list[dict],
    markdown_path: Path
) -> dict:
    """Create a merged item from a group of items."""
    chunk_ids = []
    for item in items:
        if 'chunk_ids' in item:
            chunk_ids.extend(item['chunk_ids'])
        else:
            chunk_ids.append(item['id'])

    start_line = min(item['start_line'] for item in items)
    end_line = max(item['end_line'] for item in items)
    score = max(item.get('score', item.get('final_score', 0)) for item in items)

    # Read content from file
    content = _read_content_from_file(markdown_path, start_line, end_line)

    # Get first line (heading) from first item
    first_item = items[0]
    if 'content' in first_item:
        first_line = first_item['content'].split('\n')[0]
        # Only prepend if content doesn't already start with this heading
        if not content.startswith(first_line):
            content = first_line + '\n\n' + content

    return {
        'chunk_ids': chunk_ids,
        'parent_id': items[0].get('parent_id'),
        'work_id': items[0]['work_id'],
        'content': content,
        'start_line': start_line,
        'end_line': end_line,
        'score': score
    }


def consolidate_context(
    query_id: int,
    coverage_threshold: float = DEFAULT_COVERAGE_THRESHOLD,
    line_gap: int = DEFAULT_LINE_GAP,
    verbose: bool = False
) -> ConsolidationResult:
    """Consolidate retrieved context by grouping and merging chunks.

    Args:
        query_id: ID of the Query in the database
        coverage_threshold: Threshold for replacing with parent (default 0.5)
        line_gap: Max lines between chunks to merge (default 7)
        verbose: Print progress information

    Returns:
        ConsolidationResult with consolidated groups

    Raises:
        ValueError: If query not found or no retrieved context
        RuntimeError: If markdown file hash doesn't match
    """
    with get_session() as session:
        # Fetch query
        query = session.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise ValueError(f"Query with ID {query_id} not found")

        if not query.retrieved_context:
            raise ValueError(f"Query {query_id} has no retrieved_context")

        if verbose:
            print(f"Consolidating context for query {query_id}")
            print(f"  Original items: {len(query.retrieved_context)}")

        # Get all work IDs and fetch works
        work_ids = {item['work_id'] for item in query.retrieved_context}
        works = session.query(Work).filter(Work.id.in_(work_ids)).all()
        works_map = {w.id: w for w in works}

        # Verify content hashes
        for work_id, work in works_map.items():
            if work.markdown_path and work.content_hash:
                md_path = Path(work.markdown_path)
                if md_path.exists():
                    current_hash = compute_file_hash(md_path)
                    if current_hash != work.content_hash:
                        raise RuntimeError(
                            f"Content hash mismatch for work {work_id} ({work.title}). "
                            f"File may have been modified. Cannot consolidate."
                        )

        # Get all parent chunks we need
        parent_ids = {item['parent_id'] for item in query.retrieved_context if item.get('parent_id')}
        parents = session.query(Chunk).filter(Chunk.id.in_(parent_ids)).all()
        parents_map = {p.id: p for p in parents}

        # Build hierarchy: get parents of parents for nested consolidation
        all_parent_ids = set(parent_ids)
        parents_to_check = list(parent_ids)
        while parents_to_check:
            next_level = session.query(Chunk).filter(Chunk.id.in_(parents_to_check)).all()
            parents_to_check = []
            for p in next_level:
                if p.parent_id and p.parent_id not in all_parent_ids:
                    all_parent_ids.add(p.parent_id)
                    parents_to_check.append(p.parent_id)

        # Fetch all parents
        all_parents = session.query(Chunk).filter(Chunk.id.in_(all_parent_ids)).all()
        parents_map = {p.id: p for p in all_parents}

        # Convert retrieved_context to working items
        items = []
        for ctx in query.retrieved_context:
            items.append({
                'id': ctx['id'],
                'chunk_ids': [ctx['id']],
                'parent_id': ctx.get('parent_id'),
                'work_id': ctx['work_id'],
                'content': ctx.get('content', ''),
                'start_line': ctx['start_line'],
                'end_line': ctx['end_line'],
                'score': ctx.get('final_score', 0),
                'level': ctx.get('level', 'chunk')
            })

        # Get unique levels and sort by depth (deepest first)
        parent_levels = {}
        for item in items:
            if item['parent_id'] and item['parent_id'] in parents_map:
                parent = parents_map[item['parent_id']]
                parent_levels[item['parent_id']] = parent.level

        # Process from deepest level to shallowest
        processed = True
        while processed:
            processed = False

            # Group by (work_id, parent_id)
            groups = defaultdict(list)
            for item in items:
                key = (item['work_id'], item.get('parent_id'))
                groups[key].append(item)

            new_items = []

            for (work_id, parent_id), group_items in groups.items():
                work = works_map.get(work_id)
                if not work or not work.markdown_path:
                    new_items.extend(group_items)
                    continue

                md_path = Path(work.markdown_path)
                if not md_path.exists():
                    new_items.extend(group_items)
                    continue

                # Check if parent exists
                if parent_id and parent_id in parents_map:
                    parent = parents_map[parent_id]

                    # Calculate coverage
                    coverage = _calculate_coverage(
                        group_items,
                        parent.start_line,
                        parent.end_line
                    )

                    if coverage >= coverage_threshold:
                        # Replace with parent content
                        content = _read_content_from_file(
                            md_path,
                            parent.start_line,
                            parent.end_line
                        )
                        score = max(item['score'] for item in group_items)
                        chunk_ids = []
                        for item in group_items:
                            chunk_ids.extend(item.get('chunk_ids', [item.get('id')]))

                        new_item = {
                            'chunk_ids': chunk_ids,
                            'parent_id': parent.parent_id,  # Move up one level
                            'work_id': work_id,
                            'content': content,
                            'start_line': parent.start_line,
                            'end_line': parent.end_line,
                            'score': score,
                            'level': parent.level
                        }
                        new_items.append(new_item)
                        processed = True

                        if verbose:
                            print(f"  Replaced {len(group_items)} items with parent {parent_id} ({coverage:.0%} coverage)")
                    else:
                        # Merge adjacent items
                        merged = _merge_adjacent_items(group_items, md_path, line_gap)
                        if len(merged) < len(group_items):
                            processed = True
                            if verbose:
                                print(f"  Merged {len(group_items)} items into {len(merged)} (parent {parent_id})")
                        new_items.extend(merged)
                else:
                    # No parent, just merge adjacent
                    merged = _merge_adjacent_items(group_items, md_path, line_gap)
                    if len(merged) < len(group_items):
                        processed = True
                    new_items.extend(merged)

            items = new_items

        # Build final result with heading breadcrumbs
        groups = []
        for item in items:
            # Compute heading chain from parent hierarchy
            heading_chain = _get_heading_chain(item.get('parent_id'), parents_map)

            groups.append(ConsolidatedGroup(
                chunk_ids=item.get('chunk_ids', [item.get('id')]),
                parent_id=item.get('parent_id'),
                work_id=item['work_id'],
                content=item['content'],
                start_line=item['start_line'],
                end_line=item['end_line'],
                score=item['score'],
                heading_chain=heading_chain
            ))

        # Sort by score descending
        groups.sort(key=lambda x: x.score, reverse=True)

        if verbose:
            print(f"  Consolidated count: {len(groups)}")

        # Save to database
        context_data = []
        for group in groups:
            context_data.append({
                'chunk_ids': group.chunk_ids,
                'parent_id': group.parent_id,
                'work_id': group.work_id,
                'content': group.content,
                'start_line': group.start_line,
                'end_line': group.end_line,
                'score': group.score,
                'heading_chain': ' > '.join(group.heading_chain) if group.heading_chain else None
            })

        query.clean_retrieval_context = context_data
        session.commit()

        if verbose:
            print(f"  Saved to query.clean_retrieval_context")

        return ConsolidationResult(
            query_id=query_id,
            original_count=len(query.retrieved_context),
            consolidated_count=len(groups),
            groups=groups
        )
