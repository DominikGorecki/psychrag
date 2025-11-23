# PsychRAG

A Retrieval-Augmented Generation system for psychology literature.

## Setup

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Unix/Mac

# Install package in development mode
venv\Scripts\pip install -e .
```

# Adding new Work (Asset) To DB

## 1. Convert to Markdown

### Option 1: Convert with single option

* Run `python -m psychrag.conversions.conv_pdf2md input.pdf -o putput\<file>.md`
* 


### Option 1: Convert with style and hierarchy
* Run `python -m psychrag.conversions.conv_pdf2md input.pdf -o output.md --compare -v`

## 2. Extract Bibliography and ToC

1. First preview to ensure ToC is in Char Limit: `python -m psychrag.cli.drcli bib2db <file.md> --preview --lines 123`
2. Then run without preview `python -m psychrag.cli.drcli bib2db <file.md> --lines 123`
3. This will create a new entry into the DB with the Biblio and ToC


## 3. Sanitization


1. **Extract titles:** This step extracts the titles in the markdown to ensure there is a proper hierarchy. 
    a) INPUT: Run `python -m psychrag.sanitization.extract_titles_cli <file.md>`
    b) OUTPUT: Will generate `<file>.titles.md`


2. **Suggest heading changes:** This step will use an LLM to try to determine  
    a) INPUT: Run `python -m psychrag.sanitization.suggest_heading_changes_cli <file>.titles.md`
    b) OUTPUT: will generate `<file>.title_changes.md`

    Notes: A few things here--if thee ToC is not present in the DB, this will not run properly. Need to think of a better approach when the ToC is not present as well how to improve this process:
    
    * Pass in some content under each heading until next heading -- perhaps the first 100 words and the last 100 words
    * Update prompt to specifically look for ToC based on the work title.




____________________________

# Tools

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