"""Sanitization CLI commands for heading hierarchy correction."""

import hashlib
import re
from pathlib import Path

from psychrag.data.database import SessionLocal
from psychrag.data.models import Work
from psychrag.sanitization import extract_titles_to_file, suggest_heading_changes


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


def parse_title_changes(changes_file: Path) -> dict[int, str]:
    """
    Parse a title_changes.md file to extract line number to action mapping.

    Args:
        changes_file: Path to the .title_changes.md file.

    Returns:
        Dictionary mapping line numbers to actions (NO_CHANGE, REMOVE, H1-H4).
    """
    content = changes_file.read_text(encoding='utf-8')

    # Extract the codeblock content
    codeblock_match = re.search(r'```\n(.*?)\n```', content, re.DOTALL)
    if not codeblock_match:
        raise ValueError(f"No codeblock found in: {changes_file}")

    codeblock_content = codeblock_match.group(1)

    # Parse lines matching pattern: number: ACTION
    pattern = re.compile(r'^\s*(\d+)\s*:\s*(NO_CHANGE|REMOVE|H[1-4])\s*$', re.MULTILINE)
    matches = pattern.findall(codeblock_content)

    return {int(line_num): action for line_num, action in matches}


def apply_heading_change(line: str, action: str) -> str:
    """
    Apply a heading change action to a line.

    Args:
        line: The original line of text.
        action: The action to apply (NO_CHANGE, REMOVE, H1-H4).

    Returns:
        The modified line.
    """
    if action == "NO_CHANGE":
        return line

    # Match heading pattern
    heading_match = re.match(r'^(#+)\s+(.*)$', line)
    if not heading_match:
        # Not a heading line, return as-is
        return line

    heading_text = heading_match.group(2)

    if action == "REMOVE":
        # Remove heading markers, keep the text
        return heading_text

    # Map action to heading level
    level_map = {"H1": "#", "H2": "##", "H3": "###", "H4": "####"}
    new_prefix = level_map.get(action, heading_match.group(1))

    return f"{new_prefix} {heading_text}"


def run_sanitize(input_file: str, verbose: bool = False) -> int:
    """
    Sanitize a markdown file by correcting heading hierarchy.

    Args:
        input_file: Path to the input Markdown file.
        verbose: If True, print progress information.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    input_path = Path(input_file).resolve()

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return 1

    if input_path.suffix.lower() != ".md":
        print(f"Error: Expected Markdown file (.md), got: {input_path.suffix}")
        return 1

    try:
        # Step 1: Hash the file and look up in database
        content_hash = compute_file_hash(input_path)
        if verbose:
            print(f"File hash: {content_hash}")

        with SessionLocal() as session:
            work = session.query(Work).filter(Work.content_hash == content_hash).first()
            if not work:
                print(f"Error: Document not found in database. Hash: {content_hash}")
                print("Please run bib2db first to add the document to the database.")
                return 1

            work_id = work.id
            if verbose:
                print(f"Found in database: {work.title} (id={work_id})")

        # Step 2: Generate title_changes.md if it doesn't exist
        # Derive file paths
        stem = input_path.stem
        title_changes_path = input_path.with_name(f"{stem}.title_changes.md")
        titles_path = input_path.with_name(f"{stem}.titles.md")

        if not title_changes_path.exists():
            if verbose:
                print("Generating title changes...")

            # Generate titles file if needed
            if not titles_path.exists():
                if verbose:
                    print(f"Extracting titles to: {titles_path}")
                extract_titles_to_file(input_path, titles_path)

            # Generate title changes
            if verbose:
                print(f"Suggesting heading changes...")
            suggest_heading_changes(titles_path)

            if verbose:
                print(f"Title changes saved to: {title_changes_path}")
        else:
            if verbose:
                print(f"Using existing title changes: {title_changes_path}")

        # Step 3: Apply changes to create sanitized file
        if verbose:
            print("Applying heading changes...")

        # Parse changes
        changes = parse_title_changes(title_changes_path)
        if verbose:
            print(f"Found {len(changes)} heading changes to apply")

        # Read source file
        source_lines = input_path.read_text(encoding='utf-8').splitlines()

        # Apply changes
        sanitized_lines = []
        changes_applied = 0
        for line_num, line in enumerate(source_lines, start=1):
            if line_num in changes:
                action = changes[line_num]
                new_line = apply_heading_change(line, action)
                if new_line != line:
                    changes_applied += 1
                sanitized_lines.append(new_line)
            else:
                sanitized_lines.append(line)

        # Write sanitized file
        sanitized_path = input_path.with_name(f"{stem}.sanitized.md")
        sanitized_content = '\n'.join(sanitized_lines)
        sanitized_path.write_text(sanitized_content, encoding='utf-8')

        if verbose:
            print(f"Applied {changes_applied} heading changes")
            print(f"Sanitized file saved to: {sanitized_path}")

        # Step 4: Update database
        new_hash = compute_file_hash(sanitized_path)

        with SessionLocal() as session:
            work = session.query(Work).filter(Work.id == work_id).first()
            if work:
                work.markdown_path = str(sanitized_path)
                work.content_hash = new_hash
                session.commit()
                if verbose:
                    print(f"Updated database: new hash={new_hash}")

        print(f"Sanitization complete: {sanitized_path}")
        return 0

    except Exception as e:
        print(f"Sanitization failed: {e}")
        return 1
