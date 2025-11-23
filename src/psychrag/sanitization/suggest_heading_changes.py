"""Suggest heading hierarchy changes for markdown documents.

This module uses AI to analyze markdown headings and suggest corrections
based on the table of contents stored in the database.

Usage:
    from psychrag.sanitization import suggest_heading_changes
    output_path = suggest_heading_changes("path/to/document.titles.md")

Examples:
    # Basic usage - creates document.title_changes.md
    from psychrag.sanitization import suggest_heading_changes
    result = suggest_heading_changes("book.titles.md")

Functions:
    suggest_heading_changes(titles_file) - Analyze titles and suggest hierarchy changes
"""

import json
import re
from datetime import datetime
from pathlib import Path

from psychrag.ai import create_langchain_chat, ModelTier
from psychrag.data.database import SessionLocal
from psychrag.data.models import Work
from psychrag.utils import compute_file_hash

# Directory for LLM logs
LLM_LOGS_DIR = Path("llm_logs")


def _log_llm_interaction(prompt: str, response_text: str, filename_prefix: str = "suggest_heading") -> None:
    """Log LLM prompt and response to a file.

    Args:
        prompt: The prompt sent to the LLM.
        response_text: The response received from the LLM.
        filename_prefix: Prefix for the log filename.
    """
    LLM_LOGS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LLM_LOGS_DIR / f"{filename_prefix}_{timestamp}.md"

    log_content = f"""# LLM Interaction Log
**Timestamp:** {datetime.now().isoformat()}
**Type:** {filename_prefix}

## Prompt
```
{prompt}
```

## Response
```
{response_text}
```
"""
    log_file.write_text(log_content, encoding='utf-8')


def _extract_text_from_response(response_content) -> str:
    """Extract text string from various LLM response formats.

    Args:
        response_content: The content from the LLM response (str, list, or dict).

    Returns:
        The extracted text as a string.
    """
    if isinstance(response_content, str):
        return response_content
    elif isinstance(response_content, list):
        # Handle list of content blocks
        if not response_content:
            return ""
        first_item = response_content[0]
        if isinstance(first_item, str):
            return first_item
        elif isinstance(first_item, dict):
            return first_item.get('text', str(first_item))
        else:
            return str(first_item)
    elif isinstance(response_content, dict):
        # Handle dict response (e.g., from Gemini)
        return response_content.get('text', json.dumps(response_content))
    else:
        return str(response_content)


def suggest_heading_changes(titles_file: str | Path) -> Path:
    """Analyze titles and suggest heading hierarchy changes using AI.

    Args:
        titles_file: Path to a *.titles.md file created by extract_titles_to_file.

    Returns:
        Path to the created changes file (*.title_changes.md).

    Raises:
        FileNotFoundError: If the titles file or original document is not found.
        ValueError: If the document is not found in the database.
    """
    titles_file = Path(titles_file)

    if not titles_file.exists():
        raise FileNotFoundError(f"Titles file not found: {titles_file}")

    # Parse the titles file
    content = titles_file.read_text(encoding='utf-8')
    lines = content.splitlines()

    if not lines:
        raise ValueError(f"Titles file is empty: {titles_file}")

    # First line is the relative URI to the original file
    relative_uri = lines[0].strip()

    # Resolve the original file path
    if relative_uri.startswith('./'):
        relative_uri = relative_uri[2:]
    original_path = (titles_file.parent / relative_uri).resolve()

    if not original_path.exists():
        raise FileNotFoundError(f"Original document not found: {original_path}")

    # Extract the titles codeblock
    codeblock_match = re.search(r'```\n(.*?)\n```', content, re.DOTALL)
    if not codeblock_match:
        raise ValueError(f"No titles codeblock found in: {titles_file}")

    titles_codeblock = codeblock_match.group(1)

    # Generate SHA256 hash of the original document
    content_hash = compute_file_hash(original_path)

    # Look up the document in the database
    with SessionLocal() as session:
        work = session.query(Work).filter(Work.content_hash == content_hash).first()

        if not work:
            raise ValueError(
                f"Document not found in database. Hash: {content_hash}\n"
                f"File: {original_path}"
            )

        # Extract metadata
        toc = work.toc or []
        title = work.title or "Unknown Title"
        authors = work.authors or "Unknown Author"

    # Build the LLM prompt
    prompt = _build_prompt(title, authors, toc, titles_codeblock)

    # Call LLM with web search enabled
    langchain_stack = create_langchain_chat(
        settings=None,
        tier=ModelTier.LIGHT,
        search=True,
        temperature=0.2
    )
    chat = langchain_stack.chat

    response = chat.invoke(prompt)
    response_text = _extract_text_from_response(response.content)

    # Log the interaction
    _log_llm_interaction(prompt, response_text)

    # Parse the LLM response to extract changes
    changes = _parse_llm_response(response_text)

    # Build output content
    output_lines = [
        relative_uri,
        "",
        "# CHANGES TO HEADINGS",
        "```",
        *changes,
        "```"
    ]
    output_content = "\n".join(output_lines)

    # Save to output file - use output folder
    output_dir = Path.cwd() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = titles_file.stem.replace('.titles', '')
    output_path = output_dir / f"{stem}.title_changes.md"
    output_path.write_text(output_content, encoding='utf-8')

    return output_path


def _build_prompt(title: str, authors: str, toc: list, titles_codeblock: str) -> str:
    """Build the prompt for the LLM."""

    # Format ToC for the prompt
    toc_text = ""
    if toc:
        toc_lines = []
        for item in toc:
            level = item.get('level', 1)
            item_title = item.get('title', '')
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}Level {level}: {item_title}")
        toc_text = "\n".join(toc_lines)
    else:
        toc_text = "No table of contents available"

    return f"""You are an expert at analyzing document structure and markdown formatting.

## Task
Analyze the headings from a markdown document and suggest the correct heading levels based on the document's table of contents and proper hierarchical structure.

## Document Information
- **Title:** {title}
- **Author(s):** {authors}

## Table of Contents from Database
{toc_text}

## Current Headings in Document
Each line shows: [line_number]: [current_heading]
```
{titles_codeblock}
```

## Heading Hierarchy Rules
- **H1 (#)**: Main chapters or major sections (from ToC top-level items)
- **H2 (##)**: Sections within chapters
- **H3 (###)**: Subsections
- **H4 (####)**: Sub-subsections
- **REMOVE**: Items that should not be headings (e.g., decorative text, page numbers, running headers)
- **NO_CHANGE**: Headings that are already correct

## Instructions
1. Use your knowledge of this work (if you recognize it) to understand its proper structure
2. Search the web for information about this work's structure if helpful
3. Compare the ToC from the database with the current headings
4. For each line number in the headings, determine the correct action

## Output Format
Return ONLY the changes in this exact format, one per line:
[line_number] : [ACTION] : [title_text]

Where:
- ACTION is one of: NO_CHANGE, REMOVE, H1, H2, H3, H4
- title_text is the correct title from the ToC (empty for REMOVE)
- NO_CHANGE means the heading level is correct, but still include the authoritative title text

Example:
10 : NO_CHANGE : Introduction
13 : H1 : Chapter 1: Getting Started
18 : H1 : Methods
19 : H2 : Data Collection
20 : H3 : Survey Design
25 : REMOVE :

Provide the complete list of changes for ALL headings shown above."""


def _parse_llm_response(response_text: str) -> list[str]:
    """Parse the LLM response to extract heading changes."""

    # Try to extract from a code block first if present
    codeblock_match = re.search(r'```(?:\w*\n)?(.*?)```', response_text, re.DOTALL)
    text_to_parse = codeblock_match.group(1) if codeblock_match else response_text

    # Parse line by line for more reliable extraction
    changes = []
    pattern = re.compile(r'^\s*(\d+)\s*:\s*(NO_CHANGE|REMOVE|H[1-4])\s*:\s*(.*)$')

    for line in text_to_parse.splitlines():
        match = pattern.match(line)
        if match:
            line_num = match.group(1)
            action = match.group(2)
            title = match.group(3).strip()
            changes.append(f"{line_num} : {action} : {title}")

    return changes
