"""
Extract bibliographic information from markdown files.

This module provides functionality to extract bibliographic metadata
(title, authors, publisher, etc.) from markdown documents using LLM.

Example (as library):
    from psychrag.sanitization.extract_bib import extract_bibliographic_info

    # Extract bib info
    bib_info = extract_bibliographic_info("document.md")
"""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from psychrag.ai import create_langchain_chat, LLMSettings, ModelTier
from psychrag.chunking.bib_extractor import EXTRACT_CHARS


class BibliographicInfo(BaseModel):
    """Bibliographic metadata extracted from the document."""

    title: str | None = None
    authors: list[str] = []
    publication_date: str | None = None
    publisher: str | None = None
    isbn: str | None = None
    edition: str | None = None


def extract_bibliographic_info(
    markdown_path: str | Path,
    chars: int | None = None,
    lines: int | None = None,
    settings: LLMSettings | None = None,
    tier: ModelTier = ModelTier.FULL,
) -> BibliographicInfo:
    """
    Extract bibliographic info from a markdown file.

    Args:
        markdown_path: Path to the markdown file.
        chars: Number of characters to extract from the beginning (default: EXTRACT_CHARS).
        lines: Number of lines to extract from the beginning (overrides chars if specified).
        settings: Optional LLM settings, will create default if not provided.
        tier: Model tier to use (LIGHT or FULL).

    Returns:
        BibliographicInfo with extracted metadata.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a markdown file.
    """
    markdown_path = Path(markdown_path)

    if not markdown_path.exists():
        raise FileNotFoundError(f"File not found: {markdown_path}")

    if markdown_path.suffix.lower() != ".md":
        raise ValueError(f"Expected Markdown file (.md), got: {markdown_path.suffix}")

    markdown_text = markdown_path.read_text(encoding="utf-8")

    # Determine text sample based on lines or chars
    if lines is not None:
        text_lines = markdown_text.split('\n')
        text_sample = '\n'.join(text_lines[:lines])
    else:
        if chars is None:
            chars = EXTRACT_CHARS
        text_sample = markdown_text[:chars]

    # Create LangChain chat model
    langchain_stack = create_langchain_chat(settings, tier=tier, search=True)
    chat = langchain_stack.chat

    # Create the prompt for extraction
    prompt = f"""Analyze the following text from the beginning of a document and extract bibliographic information. 
    For anything that isn't found in the document, use your intelligence or search to fill in the blanks. Bias to the copy passed it and only use your knowledge or search if necessary.

Return your response in this exact JSON format:
{{
    "title": "string or null",
    "authors": ["list of author names"],
    "publication_date": "string or null",
    "publisher": "string or null",
    "isbn": "string or null",
    "edition": "string or null"
}}

If information is not found, use null for strings and empty lists for arrays.

Text to analyze:
---
{text_sample}
---

Return only the JSON, no other text."""

    # Call the LLM
    response = chat.invoke(prompt)

    # Parse the response
    import json

    response_text = response.content
    if isinstance(response_text, list):
        response_text = response_text[0] if response_text else ""

    if isinstance(response_text, dict):
        response_text = str(response_text)

    try:
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text.strip())

        return BibliographicInfo(
            title=data.get("title"),
            authors=data.get("authors", []),
            publication_date=data.get("publication_date"),
            publisher=data.get("publisher"),
            isbn=data.get("isbn"),
            edition=data.get("edition"),
        )

    except (json.JSONDecodeError, KeyError, TypeError):
        return BibliographicInfo()
