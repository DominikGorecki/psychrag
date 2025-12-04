# Missing Tests Documentation

This document outlines all modules in the `src/` directory and identifies which tests are missing.

## Test Coverage Summary

**Existing Tests:**
- `test_augment.py` - Tests for `augmentation/augment.py`
- `test_conv_epub2md.py` - Tests for `conversions/conv_epub2md.py`
- `test_conv_pdf2md.py` - Tests for `conversions/conv_pdf2md.py`
- `test_database.py` - Tests for `data/database.py`
- `test_init_db.py` - Tests for `data/init_db.py`
- `test_inspection.py` - Tests for `conversions/inspection.py`
- `test_llm_citation_parser.py` - Tests for `utils/llm_citation_parser.py`
- `test_prompt_template_model.py` - Tests for `data/models/prompt_template.py`
- `test_rag_config_api.py` - Tests for RAG config API endpoints
- `test_rag_config_db.py` - Tests for `data/models/rag_config.py`
- `test_rag_config_integration.py` - Integration tests for RAG config
- `test_rag_config_loader.py` - Tests for `utils/rag_config_loader.py`
- `test_templates_api.py` - Tests for templates API endpoints
- `test_work_model.py` - Tests for `data/models/work.py`
- `test_api_endpoints.py` - General API endpoint tests
- `test_conversion_api_endpoints.py` - Conversion API endpoint tests

---

## Missing Tests by Package

### `psychrag/ai/` - AI Configuration and LLM Factory

#### `ai/config.py` - DONE
**Status:** ❌ Missing tests
**Functions/Classes:**
- `LLMProvider` (enum)
- `ModelTier` (enum)
- `LLMSettings` (Pydantic model)
- `_find_env_file()` (private function)
- Environment variable loading logic

**Test Requirements:**
- Test enum values and behavior
- Test Pydantic model validation
- Test environment file discovery logic
- Test settings loading from config and env files
- Test error handling for missing config/env files

#### `ai/llm_factory.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `PydanticAIStack`
- `LangChainStack`
- `LLMStack`
- `create_pydantic_agent()`
- `create_langchain_chat()`
- `create_llm_stack()`
- `create_embeddings()`

**Test Requirements:**
- Test LLM stack creation for different providers
- Test agent creation with various configurations
- Test embeddings creation
- Test error handling for invalid configurations
- Test lazy loading behavior
- Mock external API calls

---

### `psychrag/augmentation/` - RAG Augmentation

#### `augmentation/consolidate_context.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Functions for consolidating retrieval contexts
- Context merging logic
- Deduplication logic

**Test Requirements:**
- Test context consolidation logic
- Test deduplication of overlapping contexts
- Test context merging strategies
- Test edge cases (empty contexts, single context, etc.)

#### `augmentation/augment_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for augmentation
- Command-line argument parsing
- CLI workflow orchestration

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution
- Test error handling in CLI context
- Test output formatting

#### `augmentation/consolidate_context_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for context consolidation
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution
- Test error handling

---

### `psychrag/chunking/` - Document Chunking

#### `chunking/bib_extractor.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `BibliographicInfo`
- `ExtractedMetadata`
- `extract_metadata()`
- `EXTRACT_CHARS` constant

**Test Requirements:**
- Test metadata extraction from markdown
- Test bibliographic info parsing
- Test edge cases (missing metadata, malformed metadata)
- Test extraction character limits

#### `chunking/chunk_headings.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `chunk_headings()` function
- Heading hierarchy parsing
- Chunk creation logic

**Test Requirements:**
- Test heading detection and parsing
- Test hierarchy level assignment
- Test chunk boundary detection
- Test edge cases (no headings, malformed headings)

#### `chunking/chunk_headings_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for chunk_headings
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `chunking/content_chunking.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Content chunking logic
- Chunk size management
- Overlap handling

**Test Requirements:**
- Test chunk size calculation
- Test overlap handling
- Test chunk boundary detection
- Test edge cases (very short/long content)

#### `chunking/content_chunking_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for content chunking
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `chunking/extract_bib_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for bibliography extraction
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `chunking/llm_processor.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- LLM-based chunk processing
- Prompt generation for chunking
- Response parsing

**Test Requirements:**
- Test prompt generation
- Test LLM response parsing
- Test error handling for LLM failures
- Mock LLM API calls

#### `chunking/llm_processor_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for LLM processor
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `chunking/suggested_chunks.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `suggest_chunks()`
- `suggest_chunks_from_work()`
- `build_prompt_for_vec_suggestions()`
- `parse_vec_suggestions_response()`
- `save_vec_suggestions_from_response()`

**Test Requirements:**
- Test chunk suggestion logic
- Test prompt building
- Test response parsing
- Test database saving
- Mock LLM calls

#### `chunking/suggested_chunks_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for suggested chunks
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `chunking/vec_suggestions_interactive.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Interactive vector suggestions
- User interaction handling

**Test Requirements:**
- Test interactive workflow
- Test user input handling
- Test state management

---

### `psychrag/config/` - Configuration Management

#### `config/app_config.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `AppConfig`
- `DatabaseConfig`
- `LLMConfig`
- `LLMModelsConfig`
- `ModelConfig`
- `PathsConfig`
- `get_config_path()`
- `get_default_config()`
- `load_config()`
- `save_config()`

**Test Requirements:**
- Test config model validation
- Test config loading from file
- Test config saving to file
- Test default config generation
- Test config path resolution
- Test error handling for invalid configs

#### `config/app_config_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for app config
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `config/io_folder_data.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `INPUT_FORMATS`
- `OUTPUT_FORMATS`
- `IOFolderData`
- `IOFileObject`
- `ProcessedFile`
- `get_io_folder_data()`
- `get_io_folder_objects()`
- `sync_files_with_database()`

**Test Requirements:**
- Test folder scanning logic
- Test file format detection
- Test database synchronization
- Test file comparison logic
- Test edge cases (empty folders, missing files)

#### `config/io_folder_data_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for IO folder data
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

---

### `psychrag/conversions/` - Document Conversion

#### `conversions/epub_bookmarks2toc.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- EPUB bookmark to TOC conversion
- Bookmark parsing logic

**Test Requirements:**
- Test bookmark parsing
- Test TOC generation from bookmarks
- Test edge cases (no bookmarks, malformed bookmarks)

#### `conversions/new_work.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- New work creation logic
- Work initialization

**Test Requirements:**
- Test work creation
- Test database insertion
- Test validation logic
- Test error handling

#### `conversions/new_work__cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for new work creation
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `conversions/pdf_bookmarks2toc.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- PDF bookmark to TOC conversion
- Bookmark parsing logic

**Test Requirements:**
- Test bookmark parsing
- Test TOC generation from bookmarks
- Test edge cases (no bookmarks, malformed bookmarks)

#### `conversions/pdf_bookmarks2toc_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for PDF bookmark conversion
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `conversions/style_v_hier.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Style vs hierarchy analysis
- Markdown styling logic

**Test Requirements:**
- Test style detection
- Test hierarchy analysis
- Test conversion logic

#### `conversions/style_v_hier__cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for style vs hierarchy
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

---

### `psychrag/data/` - Data Models and Database

#### `data/db_health_check.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Database health check functions
- Connection testing
- Schema validation

**Test Requirements:**
- Test database connection
- Test schema validation
- Test health check reporting
- Test error handling for connection failures

#### `data/db_health_check_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for database health check
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `data/models/chunk.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `Chunk` model
- Relationships (parent, work, children)
- Vector embedding field

**Test Requirements:**
- Test model creation
- Test relationships
- Test vector field handling
- Test validation logic
- Test database operations (CRUD)

#### `data/models/io_file.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `IOFile` model
- File metadata storage

**Test Requirements:**
- Test model creation
- Test file metadata handling
- Test database operations (CRUD)

#### `data/models/prompt_meta.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `PromptMeta` model
- Prompt metadata storage

**Test Requirements:**
- Test model creation
- Test metadata handling
- Test database operations (CRUD)

#### `data/models/query.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `Query` model
- Query storage and relationships

**Test Requirements:**
- Test model creation
- Test relationships
- Test query storage
- Test database operations (CRUD)

#### `data/models/result.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `Result` model
- Result storage

**Test Requirements:**
- Test model creation
- Test result storage
- Test database operations (CRUD)

#### `data/seed_templates.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Template seeding logic
- Default template loading

**Test Requirements:**
- Test template seeding
- Test default template loading
- Test database insertion
- Test idempotency (running multiple times)

#### `data/template_loader.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Template loading logic
- Template retrieval

**Test Requirements:**
- Test template loading from database
- Test template retrieval
- Test error handling for missing templates

---

### `psychrag/retrieval/` - Query Retrieval

#### `retrieval/query_embeddings.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `vectorize_query()`
- `vectorize_all_queries()`
- `get_pending_queries_count()`
- `QueryVectorizationResult`
- `BatchVectorizationResult`

**Test Requirements:**
- Test query vectorization
- Test batch vectorization
- Test pending queries counting
- Test error handling
- Mock embedding API calls

#### `retrieval/query_embeddings_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for query embeddings
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `retrieval/query_expansion.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `expand_query()`
- `generate_expansion_prompt()`
- `parse_expansion_response()`
- `save_expansion_to_db()`
- `QueryExpansionResult`
- `ParsedExpansion`

**Test Requirements:**
- Test query expansion logic
- Test prompt generation
- Test response parsing
- Test database saving
- Mock LLM calls

#### `retrieval/query_expansion_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for query expansion
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `retrieval/retrieve.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- `retrieve()` function
- `RetrievalResult`
- `RetrievedChunk`
- Vector similarity search
- Result ranking

**Test Requirements:**
- Test retrieval logic
- Test vector similarity search
- Test result ranking
- Test top-k retrieval
- Test edge cases (no matches, empty database)

#### `retrieval/retrieve_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for retrieval
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

---

### `psychrag/sanitization/` - Content Sanitization

#### `sanitization/apply_title_changes.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Title change application logic
- Markdown modification

**Test Requirements:**
- Test title change application
- Test markdown modification
- Test validation logic
- Test error handling

#### `sanitization/apply_title_changes_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for applying title changes
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `sanitization/apply_title_edits.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Title edit application logic
- Edit processing

**Test Requirements:**
- Test edit application
- Test edit validation
- Test error handling

#### `sanitization/delete_conversion.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Conversion deletion logic
- Cascade deletion handling

**Test Requirements:**
- Test conversion deletion
- Test cascade deletion
- Test error handling for missing conversions

#### `sanitization/extract_titles.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Title extraction logic
- Markdown parsing for titles

**Test Requirements:**
- Test title extraction from markdown
- Test heading detection
- Test edge cases (no titles, malformed headings)

#### `sanitization/extract_titles_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for title extraction
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `sanitization/extract_toc.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- TOC extraction logic
- Table of contents parsing

**Test Requirements:**
- Test TOC extraction
- Test TOC parsing
- Test edge cases (no TOC, malformed TOC)

#### `sanitization/extract_toc_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for TOC extraction
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `sanitization/san_map.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Sanitization mapping logic
- Content mapping

**Test Requirements:**
- Test mapping logic
- Test content transformation
- Test error handling

#### `sanitization/san_map_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for sanitization mapping
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `sanitization/skip_apply.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Skip application logic
- Conditional processing

**Test Requirements:**
- Test skip logic
- Test conditional processing
- Test edge cases

#### `sanitization/suggest_heading_changes.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Heading change suggestion logic
- Change detection

**Test Requirements:**
- Test change detection
- Test suggestion generation
- Test validation logic

#### `sanitization/suggest_heading_changes_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for heading change suggestions
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `sanitization/suggest_heading_from_toc.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- TOC-based heading suggestion logic
- TOC analysis

**Test Requirements:**
- Test TOC analysis
- Test heading suggestion from TOC
- Test validation logic

#### `sanitization/suggest_heading_from_toc_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for TOC-based heading suggestions
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `sanitization/title_changes_interactive.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Interactive title change workflow
- User interaction handling

**Test Requirements:**
- Test interactive workflow
- Test user input handling
- Test state management

#### `sanitization/toc_titles2toc.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- TOC generation from titles
- Title to TOC conversion

**Test Requirements:**
- Test TOC generation
- Test title to TOC conversion
- Test validation logic

#### `sanitization/toc_titles2toc_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for TOC generation from titles
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `sanitization/update_content_hash.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Content hash update logic
- Hash calculation

**Test Requirements:**
- Test hash calculation
- Test hash update logic
- Test change detection

#### `sanitization/update_content_hash_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for content hash updates
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

---

### `psychrag/utils/` - Utility Functions

#### `utils/file_utils.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- File utility functions
- File operations

**Test Requirements:**
- Test file operations
- Test path handling
- Test error handling for file operations

#### `utils/file_utils_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for file utilities
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

#### `utils/model_info.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Model information retrieval
- Model metadata

**Test Requirements:**
- Test model info retrieval
- Test metadata handling
- Test error handling

#### `utils/model_info_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for model info
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

---

### `psychrag/vectorization/` - Vector Embeddings

#### `vectorization/vect_chunks.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Chunk vectorization logic
- Embedding generation
- Batch processing

**Test Requirements:**
- Test chunk vectorization
- Test embedding generation
- Test batch processing
- Test error handling
- Mock embedding API calls

#### `vectorization/vect_chunks_cli.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- CLI interface for chunk vectorization
- Command-line argument parsing

**Test Requirements:**
- Test CLI argument parsing
- Test CLI workflow execution

---

### `psychrag_api/` - FastAPI Application

#### `psychrag_api/config.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- API configuration
- Settings management

**Test Requirements:**
- Test configuration loading
- Test settings validation
- Test environment variable handling

#### `psychrag_api/dependencies.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- FastAPI dependencies
- Dependency injection

**Test Requirements:**
- Test dependency functions
- Test dependency injection
- Test error handling

#### `psychrag_api/main.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- FastAPI app initialization
- Middleware setup
- Router registration

**Test Requirements:**
- Test app initialization
- Test middleware setup
- Test router registration
- Test CORS configuration

#### `psychrag_api/routers/chunking.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Chunking API endpoints
- Request/response handling

**Test Requirements:**
- Test all endpoints
- Test request validation
- Test response formatting
- Test error handling
- Test authentication/authorization

#### `psychrag_api/routers/conversion.py`
**Status:** ⚠️ Partial coverage (see `test_conversion_api_endpoints.py`)
**Functions/Classes:**
- Conversion API endpoints
- Request/response handling

**Test Requirements:**
- Verify all endpoints are covered
- Test edge cases
- Test error handling

#### `psychrag_api/routers/corpus.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Corpus API endpoints
- Read-only corpus access

**Test Requirements:**
- Test all endpoints
- Test read-only access enforcement
- Test filtering and pagination
- Test error handling

#### `psychrag_api/routers/init.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Initialization API endpoints
- Setup endpoints

**Test Requirements:**
- Test initialization endpoints
- Test setup workflows
- Test error handling

#### `psychrag_api/routers/rag.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- RAG API endpoints
- Query and retrieval endpoints

**Test Requirements:**
- Test query endpoints
- Test retrieval endpoints
- Test augmentation endpoints
- Test error handling

#### `psychrag_api/routers/rag_config.py`
**Status:** ⚠️ Partial coverage (see `test_rag_config_api.py`)
**Functions/Classes:**
- RAG config API endpoints
- Configuration management endpoints

**Test Requirements:**
- Verify all endpoints are covered
- Test edge cases
- Test error handling

#### `psychrag_api/routers/sanitization.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Sanitization API endpoints
- Content sanitization endpoints

**Test Requirements:**
- Test all endpoints
- Test sanitization workflows
- Test error handling

#### `psychrag_api/routers/settings.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Settings API endpoints
- Configuration endpoints

**Test Requirements:**
- Test all endpoints
- Test settings management
- Test error handling

#### `psychrag_api/routers/templates.py`
**Status:** ⚠️ Partial coverage (see `test_templates_api.py`)
**Functions/Classes:**
- Templates API endpoints
- Template management endpoints

**Test Requirements:**
- Verify all endpoints are covered
- Test edge cases
- Test error handling

#### `psychrag_api/routers/vectorization.py`
**Status:** ❌ Missing tests
**Functions/Classes:**
- Vectorization API endpoints
- Embedding generation endpoints

**Test Requirements:**
- Test all endpoints
- Test vectorization workflows
- Test error handling

#### `psychrag_api/schemas/` - Pydantic Schemas
**Status:** ❌ Missing tests (all schema files)
**Files:**
- `chunking.py`
- `common.py`
- `conversion.py`
- `corpus.py`
- `init.py`
- `rag_config.py`
- `rag_queries.py`
- `rag.py`
- `sanitization.py`
- `settings.py`
- `templates.py`
- `vectorization.py`

**Test Requirements:**
- Test schema validation
- Test serialization/deserialization
- Test field validation
- Test error messages
- Test optional/required fields

---

## Test Coverage Statistics

### By Package

| Package | Total Modules | Tested | Missing | Coverage % |
|---------|--------------|--------|---------|------------|
| `psychrag/ai/` | 2 | 0 | 2 | 0% |
| `psychrag/augmentation/` | 4 | 1 | 3 | 25% |
| `psychrag/chunking/` | 12 | 0 | 12 | 0% |
| `psychrag/config/` | 4 | 0 | 4 | 0% |
| `psychrag/conversions/` | 9 | 3 | 6 | 33% |
| `psychrag/data/` | 12 | 4 | 8 | 33% |
| `psychrag/retrieval/` | 6 | 0 | 6 | 0% |
| `psychrag/sanitization/` | 20 | 0 | 20 | 0% |
| `psychrag/utils/` | 5 | 1 | 4 | 20% |
| `psychrag/vectorization/` | 2 | 0 | 2 | 0% |
| `psychrag_api/` | 20+ | 3 | 17+ | ~15% |
| **Total** | **96+** | **12** | **84+** | **~12.5%** |

### By Module Type

| Module Type | Total | Tested | Missing |
|-------------|-------|--------|---------|
| Core Logic Modules | ~50 | 8 | ~42 |
| CLI Modules | ~40 | 0 | ~40 |
| API Routers | 10 | 3 | 7 |
| API Schemas | 12 | 0 | 12 |
| Data Models | 8 | 2 | 6 |

---

## Priority Recommendations

### High Priority (Core Functionality)
1. **Data Models** (`psychrag/data/models/`)
   - `chunk.py` - Core data structure
   - `query.py` - Query storage
   - `result.py` - Result storage
   - `io_file.py` - File metadata

2. **Retrieval** (`psychrag/retrieval/`)
   - `retrieve.py` - Core retrieval logic
   - `query_expansion.py` - Query expansion
   - `query_embeddings.py` - Query vectorization

3. **Chunking** (`psychrag/chunking/`)
   - `chunk_headings.py` - Heading-based chunking
   - `content_chunking.py` - Content chunking
   - `bib_extractor.py` - Metadata extraction

4. **Vectorization** (`psychrag/vectorization/`)
   - `vect_chunks.py` - Chunk vectorization

5. **AI Configuration** (`psychrag/ai/`)
   - `llm_factory.py` - LLM creation
   - `config.py` - Configuration management

### Medium Priority (Supporting Functionality)
1. **Configuration** (`psychrag/config/`)
   - `app_config.py` - Application configuration
   - `io_folder_data.py` - File management

2. **Sanitization** (`psychrag/sanitization/`)
   - Core sanitization modules (non-CLI)

3. **Conversions** (`psychrag/conversions/`)
   - Remaining conversion modules

4. **API Schemas** (`psychrag_api/schemas/`)
   - All schema validation tests

### Lower Priority (CLI and Utilities)
1. **CLI Modules** - All `*_cli.py` files
2. **Utility Modules** - `utils/` package
3. **Interactive Modules** - Interactive workflow files

---

## Notes

- **CLI Testing**: Many CLI modules may not need extensive unit tests if they're thin wrappers around core logic. Integration tests or end-to-end tests may be more appropriate.

- **API Testing**: Some API endpoints have partial coverage. Review existing tests to ensure all endpoints and edge cases are covered.

- **Mocking**: Tests for modules that interact with external services (LLMs, embeddings, databases) should use mocks to avoid external dependencies.

- **Integration Tests**: Consider adding integration tests for workflows that span multiple modules (e.g., conversion → chunking → vectorization → retrieval).

- **Test Organization**: Consider organizing tests to mirror the source structure (e.g., `tests/unit/ai/`, `tests/unit/chunking/`, etc.) for better maintainability.

