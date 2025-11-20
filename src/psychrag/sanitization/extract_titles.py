"""Extract markdown titles from a document.

This module provides functionality to extract all titles (headings) from a markdown
file and save them to a separate file with line numbers for hierarchy analysis.

Usage:
    from psychrag.sanitization import extract_titles_to_file, extract_titles
    output_path = extract_titles_to_file("path/to/document.md")
    titles = extract_titles("path/to/document.md")

Examples:
    # Basic usage - creates document.titles.md
    from psychrag.sanitization import extract_titles_to_file
    result = extract_titles_to_file("book.md")

    # Get titles as list without writing to file
    from psychrag.sanitization import extract_titles
    titles = extract_titles("book.md")

    # Custom output path
    result = extract_titles_to_file("book.md", "output/titles.md")

Functions:
    extract_titles(input_path) - Extract titles and return as list
    extract_titles_to_file(input_path, output_path) - Extract titles to file
"""

import re
from pathlib import Path


def _validate_input(input_path: Path) -> None:
    """Validate input file exists and is markdown.

    Args:
        input_path: Path to validate.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a markdown file.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_path.suffix.lower() not in ('.md', '.markdown'):
        raise ValueError(f"Input file must be a markdown file: {input_path}")


def _extract_titles_from_content(content: str) -> list[str]:
    """Extract titles from markdown content.

    Args:
        content: Markdown content as string.

    Returns:
        List of strings in format "line_num: heading_line".
    """
    lines = content.splitlines()
    title_pattern = re.compile(r'^#+\s+')
    titles = []

    for line_num, line in enumerate(lines, start=1):
        if title_pattern.match(line):
            titles.append(f"{line_num}: {line}")

    return titles


def extract_titles(input_path: str | Path) -> list[str]:
    """Extract all titles from a markdown file.

    Args:
        input_path: Path to the markdown file to analyze.

    Returns:
        List of strings in format "line_num: heading_line".

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a markdown file.
    """
    input_path = Path(input_path)
    _validate_input(input_path)

    content = input_path.read_text(encoding='utf-8')
    return _extract_titles_from_content(content)


def extract_titles_to_file(
    input_path: str | Path,
    output_path: str | Path | None = None
) -> Path:
    """Extract all titles from a markdown file and save to a titles file.

    Args:
        input_path: Path to the markdown file to analyze.
        output_path: Optional path for the output file. If not provided,
            will use the input filename with '.titles.md' suffix.

    Returns:
        Path to the created titles file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a markdown file.
    """
    input_path = Path(input_path)
    _validate_input(input_path)

    # Determine output path
    if output_path is None:
        output_path = input_path.with_suffix('.titles.md')
    else:
        output_path = Path(output_path)

    # Extract titles
    content = input_path.read_text(encoding='utf-8')
    titles = _extract_titles_from_content(content)

    # Calculate relative path from output to input
    try:
        relative_uri = input_path.relative_to(output_path.parent)
        relative_uri_str = f"./{relative_uri.as_posix()}"
    except ValueError:
        # Files are on different drives or can't be made relative
        relative_uri_str = input_path.as_posix()

    # Build output content
    output_lines = [
        relative_uri_str,
        "",
        "# ALL TITLES IN DOC",
        "```",
        *titles,
        "```"
    ]

    output_content = "\n".join(output_lines)

    # Write output file
    output_path.write_text(output_content, encoding='utf-8')

    return output_path
