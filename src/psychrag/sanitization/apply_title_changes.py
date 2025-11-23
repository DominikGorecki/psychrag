"""
Apply title changes to markdown documents.

This module applies heading changes from a .title_changes.md file to the
original markdown document, creating a sanitized version.

Usage:
    from psychrag.sanitization.apply_title_changes import apply_title_changes, preview_title_changes

    # Preview changes
    preview = preview_title_changes("book.title_changes.md", work_id=1)

    # Apply changes
    output_path = apply_title_changes("book.title_changes.md", work_id=1)
"""

import re
from pathlib import Path

from psychrag.data.database import SessionLocal
from psychrag.data.models import Work
from psychrag.utils import compute_file_hash, set_file_readonly


def parse_title_changes(changes_file: str | Path) -> tuple[str, list[dict]]:
    """
    Parse a .title_changes.md file.

    Args:
        changes_file: Path to the .title_changes.md file.

    Returns:
        Tuple of (relative_uri, list of change dicts).
        Each change dict has: line_num, action, title_text

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file format is invalid.
    """
    changes_file = Path(changes_file)

    if not changes_file.exists():
        raise FileNotFoundError(f"Changes file not found: {changes_file}")

    content = changes_file.read_text(encoding='utf-8')
    lines = content.splitlines()

    if not lines:
        raise ValueError(f"Changes file is empty: {changes_file}")

    # First line is the relative URI
    relative_uri = lines[0].strip()

    # Extract the changes codeblock
    codeblock_match = re.search(r'```\n(.*?)\n```', content, re.DOTALL)
    if not codeblock_match:
        raise ValueError(f"No changes codeblock found in: {changes_file}")

    changes_text = codeblock_match.group(1)

    # Parse each change line
    changes = []
    pattern = re.compile(r'^\s*(\d+)\s*:\s*(NO_CHANGE|REMOVE|H[1-4])\s*:\s*(.*?)\s*$')

    for line in changes_text.splitlines():
        match = pattern.match(line)
        if match:
            changes.append({
                'line_num': int(match.group(1)),
                'action': match.group(2),
                'title_text': match.group(3)
            })

    return relative_uri, changes


def preview_title_changes(
    changes_file: str | Path,
    work_id: int,
) -> list[dict]:
    """
    Preview title changes without applying them.

    Args:
        changes_file: Path to the .title_changes.md file.
        work_id: ID of the Work record in the database.

    Returns:
        List of preview dicts with: line_num, old_line, new_line

    Raises:
        FileNotFoundError: If files are not found.
        ValueError: If work not found or file format invalid.
    """
    changes_file = Path(changes_file)
    relative_uri, changes = parse_title_changes(changes_file)

    # Get the markdown path from the database
    with SessionLocal() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work with ID {work_id} not found")
        if not work.markdown_path:
            raise ValueError(f"Work {work_id} has no markdown_path")

        markdown_path = Path(work.markdown_path)

    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    # Read the original markdown
    original_content = markdown_path.read_text(encoding='utf-8')
    original_lines = original_content.splitlines()

    # Build preview
    previews = []
    for change in changes:
        line_num = change['line_num']
        action = change['action']
        title_text = change['title_text']

        if line_num < 1 or line_num > len(original_lines):
            continue

        old_line = original_lines[line_num - 1]

        if action == 'REMOVE':
            new_line = "[REMOVED]"
        elif action == 'NO_CHANGE':
            # Keep original level, but update text
            level_match = re.match(r'^(#+)\s+', old_line)
            if level_match:
                prefix = level_match.group(1)
                new_line = f"{prefix} {title_text}"
            else:
                new_line = old_line
        else:
            # H1, H2, H3, H4
            level = int(action[1])
            prefix = '#' * level
            new_line = f"{prefix} {title_text}"

        previews.append({
            'line_num': line_num,
            'old_line': old_line,
            'new_line': new_line
        })

    return previews


def apply_title_changes(
    changes_file: str | Path,
    work_id: int,
) -> Path:
    """
    Apply title changes to create a sanitized markdown file.

    Args:
        changes_file: Path to the .title_changes.md file.
        work_id: ID of the Work record in the database.

    Returns:
        Path to the created sanitized file.

    Raises:
        FileNotFoundError: If files are not found.
        ValueError: If work not found or file format invalid.
    """
    changes_file = Path(changes_file)
    relative_uri, changes = parse_title_changes(changes_file)

    # Get the markdown path from the database
    with SessionLocal() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work with ID {work_id} not found")
        if not work.markdown_path:
            raise ValueError(f"Work {work_id} has no markdown_path")

        markdown_path = Path(work.markdown_path)

    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    # Read the original markdown
    original_content = markdown_path.read_text(encoding='utf-8')
    original_lines = original_content.splitlines()

    # Build a map of line numbers to changes
    changes_map = {c['line_num']: c for c in changes}

    # Apply changes
    new_lines = []
    for i, line in enumerate(original_lines, start=1):
        if i in changes_map:
            change = changes_map[i]
            action = change['action']
            title_text = change['title_text']

            if action == 'REMOVE':
                # Skip this line (remove it)
                continue
            elif action == 'NO_CHANGE':
                # Keep original level, update text
                level_match = re.match(r'^(#+)\s+', line)
                if level_match:
                    prefix = level_match.group(1)
                    new_lines.append(f"{prefix} {title_text}")
                else:
                    new_lines.append(line)
            else:
                # H1, H2, H3, H4
                level = int(action[1])
                prefix = '#' * level
                new_lines.append(f"{prefix} {title_text}")
        else:
            new_lines.append(line)

    # Create sanitized file
    sanitized_path = markdown_path.with_name(
        markdown_path.stem + '.sanitized.md'
    )
    sanitized_content = '\n'.join(new_lines)
    sanitized_path.write_text(sanitized_content, encoding='utf-8')

    # Compute new hash and update database
    new_hash = compute_file_hash(sanitized_path)

    with SessionLocal() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        work.content_hash = new_hash
        work.markdown_path = str(sanitized_path.absolute())
        session.commit()

    # Set file to read-only
    set_file_readonly(sanitized_path)

    return sanitized_path
