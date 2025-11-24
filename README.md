# PsychRAG

A Retrieval-Augmented Generation system for psychology literature.

## Setup

### 1. Environment and Packages Install

Activate setup and activate the environment (recommended):

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Unix/Mac
```

Install the packages--this will take some time and requires ~2GB of space just for the install -- probably close to 15GB more when running and different models are downloaded on the fly. 

```
# Install package in development mode
venv\Scripts\pip install -e .
```

### 2. Settings (.env) File
| Note: Currently only supporting gemini api. 

Create a .env file in the root-folder where this file exists with the following template:
```
# PostgreSQL Connection Configuration
# Admin credentials (for database/user creation)
POSTGRES_ADMIN_USER=postgres
POSTGRES_ADMIN_PASSWORD=postgres
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

# Application database
POSTGRES_DB=psych_rag

# Application user (will be created by init_db)
POSTGRES_APP_USER=psych_rag_app_user
POSTGRES_APP_PASSWORD=psych_rag_secure_password

# LLM Provider Configuration
# Only Gemini currently supported
LLM_PROVIDER=gemini

# OpenAI -- currently not supported -- feel free to skip
LLM_OPENAI_API_KEY=
LLM_OPENAI_LIGHT_MODEL=gpt-4.1-mini
LLM_OPENAI_FULL_MODEL=gpt-4o

# Gemini -- currently required
LLM_GOOGLE_API_KEY=[YOUR API KEY]
# Gemini fast/light model -- feel free to adjust:
LLM_GEMINI_LIGHT_MODEL=gemini-flash-latest 
# Gemini full/thinking model -- feel free to adjust:
LLM_GEMINI_FULL_MODEL=gemini-2.5-pro
```

TODO: Add support to OpenAI as a provider. In the future, others. 

### 3. Initiate the Database and Filesystem

Use the `init_db` module to initiate the DB:

```bash
python -m psychrag.data.init_db -v
```

Add an `output` folder to the rood of the repo.

```bash
mkdir output
```

TODO: Make the output path configurable in .env file. 

# Adding new Work (Asset) To DB

## 1. Convert to Markdown - From PDF

* Conversion can take time depending on your setup--
* For the output filename:
    * Keep the file simple--you'll need to reference it multiple times
    * Don't use spaces: `this file.md` should be `this_file.md`
    * Don't use special chars, etc. -- I didn't test this, plus keep it simple.
    * Don't worry about keeping meta information in the title -- the bibliography of the work will be pulled into the DB. As long as you just know the filename during the ingestion process--after it won't matter. 
    * **Don't delete any files from the `output` folder manually**


OSS Examples to try:
* https://en.wikibooks.org/wiki/Cognitive_Psychology_and_Cognitive_Neuroscience (pdf link)


### Option 1: Convert with single option

* Run `python -m psychrag.conversions.conv_pdf2md raw\input.pdf -o output\<file>.md`
* This generates `<file>.md`


### Option 2: Convert with style and hierarchy (recommended)
* Run `python -m psychrag.conversions.conv_pdf2md raw\input.pdf -o output\<file>.md --compare -v`
* This generates `<file>.style.md` and `<file>.hier.md`

**Choose the better result**
* AutomatedRun `python -m psychrag.conversions.style_v_hier__cli output\<file>.style.md output\<file>.hier.md -v` that runs heuristic to pick the better candidate
* Manual: Scroll through both markdown files and manually choose the best one. Rename the `style` or `hier` to just `<file>.md`. Choose the file that better

## 2. Extract Bibliography and ToC

Now we need to update the DB to pull out the bibliography and  

1. First preview to ensure ToC is in Char Limit: `python -m psychrag.chunking.extract_bib_cli <file>.md --preview --lines ###`

`python -m psychrag.cli.drcli bib2db <file.md> --preview --lines 123`
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

## 4. Chunking
1. Suggest vectorization: `python -m psychrag.chunking.suggested_chunks_cli <work>.md`

2. Chunk Headings into DB: `python -m psychrag.chunking.chunk_headings_cli 4 -v`

3. Chunk Content into DB: `python -m psychrag.chunking.content_chunking_cli 4 -v`

## 5. Vectorizing
1. python -m psychrag.vectorization.vect_chunks_cli <work_id> 




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