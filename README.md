# PsychRAG

A Retrieval-Augmented Generation system for psychology literature.

## Setup

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Unix/Mac

# Install package in development mode
venv\Scripts\pip install -r requirements.txt
```

## Tools

### conv_epub2md - EPUB to Markdown Converter

Converts EPUB files to Markdown format using Docling.

#### As a Script

```bash
# Output to stdout
venv\Scripts\python -m psychrag.conversions.conv_epub2md book.epub

# Output to file
venv\Scripts\python -m psychrag.conversions.conv_epub2md book.epub -o output.md

# Verbose mode
venv\Scripts\python -m psychrag.conversions.conv_epub2md book.epub -o output.md -v
```

#### As a Library

```python
from psychrag.conversions import convert_epub_to_markdown

# Get markdown as string
markdown_content = convert_epub_to_markdown("book.epub")

# Save to file
convert_epub_to_markdown("book.epub", output_path="output.md")

# With verbose output
markdown_content = convert_epub_to_markdown("book.epub", verbose=True)
```

### conv_pdf2md - PDF to Markdown Converter

Converts PDF files to Markdown format using Docling.

#### As a Script

```bash
# Output to stdout
venv\Scripts\python -m psychrag.conversions.conv_pdf2md document.pdf

# Output to file
venv\Scripts\python -m psychrag.conversions.conv_pdf2md document.pdf -o output.md

# Verbose mode
venv\Scripts\python -m psychrag.conversions.conv_pdf2md document.pdf -o output.md -v
```

#### As a Library

```python
from psychrag.conversions import convert_pdf_to_markdown

# Get markdown as string
markdown_content = convert_pdf_to_markdown("document.pdf")

# Save to file
convert_pdf_to_markdown("document.pdf", output_path="output.md")

# With verbose output
markdown_content = convert_pdf_to_markdown("document.pdf", verbose=True)
```

## Testing

```bash
venv\Scripts\pytest
```