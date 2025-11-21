"""Suggest which document sections should be chunked and vectorized.

This module analyzes markdown document headings and uses an LLM to determine
which sections contain valuable content worth vectorizing versus sections
like table of contents, indexes, and references that should be skipped.

Usage:
    from psychrag.chunking.suggested_chunks import suggest_chunks
    output_path = suggest_chunks("path/to/document.sanitized.md")

Examples:
    # Basic usage - creates document.sanitized.vectorize_suggestions.md
    from psychrag.chunking.suggested_chunks import suggest_chunks
    result = suggest_chunks("book.sanitized.md")

    # With bibliographic info for better context
    from psychrag.chunking import BibliographicInfo
    bib = BibliographicInfo(title="My Book", authors=["Author"])
    result = suggest_chunks("book.sanitized.md", bib_info=bib)

Functions:
    suggest_chunks(input_path, bib_info) - Analyze and suggest vectorization
"""

import re
from pathlib import Path

from psychrag.ai import create_langchain_chat, ModelTier
from psychrag.chunking.bib_extractor import BibliographicInfo
from psychrag.sanitization.extract_titles import extract_titles_to_file


def _build_prompt(titles_content: str, bib_info: BibliographicInfo | None) -> str:
    """Build the LLM prompt for analyzing titles.

    Args:
        titles_content: The titles codeblock content.
        bib_info: Optional bibliographic information about the work.

    Returns:
        Formatted prompt string.
    """
    bib_section = ""
    if bib_info:
        bib_parts = []
        if bib_info.title:
            bib_parts.append(f"Title: {bib_info.title}")
        if bib_info.authors:
            bib_parts.append(f"Authors: {', '.join(bib_info.authors)}")
        if hasattr(bib_info, 'publication_date') and bib_info.publication_date:
            bib_parts.append(f"Publication Date: {bib_info.publication_date}")
        if hasattr(bib_info, 'year') and bib_info.year:
            bib_parts.append(f"Year: {bib_info.year}")
        if bib_info.publisher:
            bib_parts.append(f"Publisher: {bib_info.publisher}")
        if bib_section:
            bib_section = "## Bibliographic Information\n" + "\n".join(bib_parts) + "\n\n"

    prompt = f"""You are analyzing a document's heading structure to determine which sections contain valuable content worth vectorizing for a RAG (Retrieval Augmented Generation) system.

{bib_section}## Document Headings

{titles_content}

## Task

For each heading line number, determine whether it should be:
- **VECTORIZE**: Contains valuable content that should be chunked and stored in a vector database
- **SKIP**: Contains non-valuable content like table of contents, indexes, references, bibliographies, appendices with reference data, or other structural/navigational content

## Guidelines

1. Content to SKIP:
   - Table of Contents (ToC)
   - Indexes (subject index, author index, etc.)
   - References and bibliographies
   - Appendices containing only reference data
   - Front matter (title pages, copyright, dedications)
   - Back matter with purely structural content

2. Content to VECTORIZE:
   - Chapters with actual content
   - Sections explaining concepts, theories, or information
   - Any content that would be useful for answering questions about the subject matter

## Output Format

Return ONLY a list in this exact format, one line per heading:
```
[line_number]: [SKIP|VECTORIZE]
```

Example:
```
10: SKIP
13: SKIP
18: VECTORIZE
19: VECTORIZE
20: VECTORIZE
```

Analyze the headings and provide your recommendations:"""

    return prompt


def _parse_heading_level(line: str) -> int:
    """Extract heading level from a title line.

    Args:
        line: A line like "10: # Title" or "10: ### Subsection"

    Returns:
        Heading level (1-6) or 0 if not a heading.
    """
    # Match the heading after the line number
    match = re.search(r':\s*(#+)', line)
    if match:
        return len(match.group(1))
    return 0


def _parse_llm_response(response: str) -> dict[int, str]:
    """Parse LLM response into line number to decision mapping.

    Args:
        response: LLM response text.

    Returns:
        Dictionary mapping line numbers to SKIP/VECTORIZE decisions.
    """
    decisions = {}

    # Extract content from code blocks if present
    if "```" in response:
        blocks = re.findall(r'```(?:\w*\n)?(.*?)```', response, re.DOTALL)
        if blocks:
            response = blocks[-1]  # Use last code block

    # Parse each line
    for line in response.strip().split('\n'):
        match = re.match(r'(\d+):\s*(SKIP|VECTORIZE)', line.strip(), re.IGNORECASE)
        if match:
            line_num = int(match.group(1))
            decision = match.group(2).upper()
            decisions[line_num] = decision

    return decisions


def _apply_hierarchy_rules(
    decisions: dict[int, str],
    titles: list[str]
) -> dict[int, str]:
    """Apply hierarchy rules to decisions.

    Rules:
    - If a parent (H1/H2) is SKIP, all children should be SKIP
    - If any child is VECTORIZE, the parent should be VECTORIZE

    Args:
        decisions: Initial decisions from LLM.
        titles: List of title lines with line numbers.

    Returns:
        Updated decisions with hierarchy rules applied.
    """
    # Parse titles into structured format
    parsed = []
    for title in titles:
        match = re.match(r'(\d+):\s*(#+)', title)
        if match:
            line_num = int(match.group(1))
            level = len(match.group(2))
            parsed.append((line_num, level))

    if not parsed:
        return decisions

    result = decisions.copy()

    # First pass: propagate SKIP down
    for i, (line_num, level) in enumerate(parsed):
        if result.get(line_num) == 'SKIP':
            # Mark all children as SKIP
            for j in range(i + 1, len(parsed)):
                child_num, child_level = parsed[j]
                if child_level > level:
                    result[child_num] = 'SKIP'
                else:
                    break  # No longer a child

    # Second pass: propagate VECTORIZE up
    for i in range(len(parsed) - 1, -1, -1):
        line_num, level = parsed[i]
        if result.get(line_num) == 'VECTORIZE':
            # Find parent and mark as VECTORIZE
            for j in range(i - 1, -1, -1):
                parent_num, parent_level = parsed[j]
                if parent_level < level:
                    result[parent_num] = 'VECTORIZE'
                    level = parent_level  # Continue up the hierarchy

    return result


def suggest_chunks(
    input_path: str | Path,
    bib_info: BibliographicInfo | None = None,
    verbose: bool = False
) -> Path:
    """Analyze document headings and suggest which sections to vectorize.

    Args:
        input_path: Path to the sanitized markdown file.
        bib_info: Optional bibliographic information for context.
        verbose: Whether to print progress information.

    Returns:
        Path to the created suggestions file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input file is not a markdown file.
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_path.suffix.lower() not in ('.md', '.markdown'):
        raise ValueError(f"Input file must be a markdown file: {input_path}")

    # Step 1: Extract titles
    if verbose:
        print(f"Extracting titles from {input_path.name}...")

    titles_path = extract_titles_to_file(input_path)

    if verbose:
        print(f"Titles saved to {titles_path.name}")

    # Step 2: Read titles content
    titles_content = titles_path.read_text(encoding='utf-8')

    # Extract the titles list from the file
    titles_match = re.search(r'```\n(.*?)```', titles_content, re.DOTALL)
    if not titles_match:
        raise ValueError("Could not find titles codeblock in titles file")

    titles_block = titles_match.group(1).strip()
    titles_list = titles_block.split('\n')

    # Step 3: Build and send prompt to LLM
    if verbose:
        print("Analyzing headings with LLM...")

    prompt = _build_prompt(titles_block, bib_info)

    langchain_stack = create_langchain_chat(
        settings=None,
        tier=ModelTier.LIGHT,
        search=True,
        temperature=0.2
    )

    response = langchain_stack.chat.invoke(prompt)
    response_text = response.content

    # Handle case where content might be a list
    if isinstance(response_text, list):
        response_text = '\n'.join(str(item) for item in response_text)

    # Step 4: Parse response and apply hierarchy rules
    decisions = _parse_llm_response(response_text)
    decisions = _apply_hierarchy_rules(decisions, titles_list)

    # Step 5: Build output content
    output_lines = ["# CHANGES TO HEADINGS", "```"]

    for title in titles_list:
        match = re.match(r'(\d+):', title)
        if match:
            line_num = int(match.group(1))
            decision = decisions.get(line_num, 'VECTORIZE')  # Default to VECTORIZE
            output_lines.append(f"{line_num}: {decision}")

    output_lines.append("```")
    output_content = "\n".join(output_lines)

    # Step 6: Save output
    output_path = input_path.with_suffix('.vectorize_suggestions.md')
    output_path.write_text(output_content, encoding='utf-8')

    if verbose:
        print(f"Suggestions saved to {output_path.name}")

    return output_path
