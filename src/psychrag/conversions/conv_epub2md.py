"""
EPUB to Markdown Converter using Docling and ebooklib.

This module provides functionality to convert EPUB files to Markdown format.
It extracts HTML content from EPUB files using ebooklib and then converts
the HTML to Markdown using Docling.

Example (as script):
    venv\\Scripts\\python conv_epub2md.py input.epub -o output.md

Example (as library):
    from conv_epub2md import convert_epub_to_markdown
    markdown_content = convert_epub_to_markdown("input.epub")
"""

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Optional

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from docling.document_converter import DocumentConverter


def _extract_epub_to_html(epub_path: Path) -> str:
    """
    Extract all text content from an EPUB file as a single well-formed HTML.

    Args:
        epub_path: Path to the EPUB file.

    Returns:
        Combined HTML content from all document items as a single HTML document.
    """
    book = epub.read_epub(str(epub_path))

    # Collect body content from all document items
    body_parts = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = item.get_content().decode("utf-8", errors="ignore")
        soup = BeautifulSoup(content, "html.parser")

        # Remove internal anchor links (links to .html files or # anchors)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            # Remove links to internal HTML files or anchors
            if href.startswith("#") or href.endswith(".html") or ".html#" in href:
                # Replace anchor with its text content
                a_tag.unwrap()

        # Extract body content
        body = soup.find("body")
        if body:
            # Get inner HTML of body
            body_parts.append(str(body))

    # Create a single well-formed HTML document
    combined_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Converted EPUB</title>
</head>
<body>
{"".join(body_parts)}
</body>
</html>"""

    return combined_html


def convert_epub_to_markdown(
    epub_path: str | Path,
    output_path: Optional[str | Path] = None,
    verbose: bool = False
) -> str:
    """
    Convert an EPUB file to Markdown format.

    Args:
        epub_path: Path to the input EPUB file.
        output_path: Optional path for the output Markdown file.
                    If provided, the markdown will be written to this file.
        verbose: If True, print progress information.

    Returns:
        The converted Markdown content as a string.

    Raises:
        FileNotFoundError: If the EPUB file does not exist.
        ValueError: If the file is not an EPUB file.
    """
    epub_path = Path(epub_path)

    # Validate input file
    if not epub_path.exists():
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")

    if epub_path.suffix.lower() != ".epub":
        raise ValueError(f"File must be an EPUB file, got: {epub_path.suffix}")

    if verbose:
        print(f"Converting: {epub_path}")

    # Extract HTML from EPUB
    html_content = _extract_epub_to_html(epub_path)

    # Create temporary HTML file for Docling to process
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        delete=False,
        encoding="utf-8"
    ) as tmp_file:
        tmp_file.write(html_content)
        tmp_path = tmp_file.name

    try:
        # Initialize converter and convert HTML
        converter = DocumentConverter()
        result = converter.convert(tmp_path)

        # Export to markdown
        markdown_content = result.document.export_to_markdown()
    finally:
        # Clean up temporary file
        Path(tmp_path).unlink(missing_ok=True)

    # Write to output file if specified
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding="utf-8")
        if verbose:
            print(f"Output written to: {output_path}")

    return markdown_content


def main() -> int:
    """
    Main entry point for the command-line interface.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Convert EPUB files to Markdown using Docling.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s book.epub                    # Output to stdout
  %(prog)s book.epub -o book.md         # Output to file
  %(prog)s book.epub -o output/book.md  # Output to subdirectory
  %(prog)s book.epub -v                 # Verbose output
        """
    )

    parser.add_argument(
        "epub_path",
        type=str,
        help="Path to the input EPUB file"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Path for the output Markdown file (default: print to stdout)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )

    args = parser.parse_args()

    try:
        markdown_content = convert_epub_to_markdown(
            epub_path=args.epub_path,
            output_path=args.output,
            verbose=args.verbose
        )

        # Print to stdout if no output file specified
        if not args.output:
            print(markdown_content)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
