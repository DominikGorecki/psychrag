# Pre-Release Audit: PsychRAG Open Source Preparation

**Date:** 2025-01-XX  
**Purpose:** Identify improvements needed before open-sourcing the PsychRAG project

---

## Executive Summary

This document identifies modules not used by the UI, standardization opportunities, and other improvements needed before releasing PsychRAG as an open-source project. The analysis covers:

- **Backend Python modules** (`src/psychrag/`)
- **API layer** (`src/psychrag_api/`)
- **Frontend UI** (`psychrag_ui/`)
- **CLI tools** (27 CLI modules identified)

---

## 1. Modules Not Used in UI

### 1.1 CLI Modules (Backend Only)

The following CLI modules exist but are **not called from the UI**. They are accessible via command-line only and may be useful for:
- Development/debugging
- Batch operations
- Direct library usage
- Legacy workflows

#### Conversion CLI Modules
- `src/psychrag/conversions/new_work__cli.py` - **USED** (via API endpoint `/conv/add-to-database`)
- `src/psychrag/conversions/style_v_hier__cli.py` - **USED** (via API endpoint `/conv/suggestion/{file_id}`)
- `src/psychrag/conversions/pdf_bookmarks2toc_cli.py` - **NOT USED** (no API endpoint)
- `src/psychrag/conversions/conv_epub2md.py` - **USED** (has `if __name__ == "__main__"` block, also via API)
- `src/psychrag/conversions/conv_pdf2md.py` - **USED** (has `if __name__ == "__main__"` block, also via API)

#### Chunking CLI Modules
- `src/psychrag/chunking/chunk_headings_cli.py` - **USED** (via API endpoint `/chunk/work/{work_id}/apply-heading-chunks`)
- `src/psychrag/chunking/content_chunking_cli.py` - **USED** (via API endpoint `/chunk/work/{work_id}/apply-content-chunks`)
- `src/psychrag/chunking/suggested_chunks_cli.py` - **USED** (via API endpoint `/chunk/work/{work_id}/vec-suggestions/run`)
- `src/psychrag/chunking/extract_bib_cli.py` - **NOT USED** (marked as DEPRECATING in docstring)
- `src/psychrag/chunking/llm_processor_cli.py` - **NOT USED** (no API endpoint)

#### Sanitization CLI Modules
- `src/psychrag/sanitization/extract_titles_cli.py` - **USED** (via API endpoint `/chunk/work/{work_id}/extract-sanitized-titles`)
- `src/psychrag/sanitization/suggest_heading_changes_cli.py` - **USED** (via API endpoint `/sanitization/work/{work_id}/prompt`)
- `src/psychrag/sanitization/suggest_heading_from_toc_cli.py` - **NOT USED** (no API endpoint)
- `src/psychrag/sanitization/apply_title_changes_cli.py` - **USED** (via API endpoint `/sanitization/work/{work_id}/apply-title-changes`)
- `src/psychrag/sanitization/update_content_hash_cli.py` - **NOT USED** (no API endpoint)
- `src/psychrag/sanitization/toc_titles2toc_cli.py` - **NOT USED** (no API endpoint)
- `src/psychrag/sanitization/san_map_cli.py` - **NOT USED** (no API endpoint)
- `src/psychrag/sanitization/extract_toc_cli.py` - **NOT USED** (no API endpoint)

#### Vectorization CLI Modules
- `src/psychrag/vectorization/vect_chunks_cli.py` - **USED** (via API endpoint `/vec/vectorize`)

#### Retrieval CLI Modules
- `src/psychrag/retrieval/query_expansion_cli.py` - **USED** (via API endpoint `/rag/expansion/run`)
- `src/psychrag/retrieval/query_embeddings_cli.py` - **USED** (via API endpoint `/rag/queries/{id}/embed`)
- `src/psychrag/retrieval/retrieve_cli.py` - **USED** (via API endpoint `/rag/queries/{id}/retrieve`)

#### Augmentation CLI Modules
- `src/psychrag/augmentation/consolidate_context_cli.py` - **USED** (via API endpoint `/rag/queries/{id}/consolidate`)
- `src/psychrag/augmentation/augment_cli.py` - **USED** (via API endpoint `/rag/queries/{id}/augment/run`)

#### Config/Utils CLI Modules
- `src/psychrag/config/app_config_cli.py` - **NOT USED** (no API endpoint, but useful for CLI config management)
- `src/psychrag/config/io_folder_data_cli.py` - **NOT USED** (no API endpoint)
- `src/psychrag/data/db_health_check_cli.py` - **USED** (via API endpoint `/init/db-health`)
- `src/psychrag/utils/file_utils_cli.py` - **NOT USED** (no API endpoint)
- `src/psychrag/utils/model_info_cli.py` - **NOT USED** (no API endpoint)

### 1.2 Summary: Unused CLI Modules

**Total CLI modules:** 27  
**Used via API:** 18  
**Not used in UI:** 9

#### Recommended Actions:

1. **Keep for CLI users:**
   - `app_config_cli.py` - Useful for configuration management
   - `file_utils_cli.py` - Utility tool
   - `model_info_cli.py` - Debugging tool

2. **Consider removing (deprecated/unused):**
   - `extract_bib_cli.py` - Marked as DEPRECATING
   - `llm_processor_cli.py` - No clear use case
   - `suggest_heading_from_toc_cli.py` - Functionality may be covered elsewhere
   - `update_content_hash_cli.py` - Internal operation, may not need CLI
   - `toc_titles2toc_cli.py` - Functionality may be covered in conversion flow
   - `san_map_cli.py` - May be superseded by other sanitization methods
   - `extract_toc_cli.py` - Functionality may be covered in conversion flow
   - `pdf_bookmarks2toc_cli.py` - May be integrated into conversion flow
   - `io_folder_data_cli.py` - May be internal utility

3. **Documentation needed:**
   - Document which CLI tools are intended for end users vs. developers
   - Create a CLI reference guide
   - Mark deprecated modules clearly

---

## 2. Standardization Opportunities

### 2.1 Naming Inconsistencies

#### Directory Naming: `vectorizing` vs `vectorization`
- **Issue:** Documentation (`.cursorrules`, `project-structure.md`) references `vectorizing/` directory
- **Reality:** Actual directory is `vectorization/`
- **Impact:** Confusing for new contributors
- **Recommendation:** 
  - Update all documentation to use `vectorization/`
  - Or rename directory to match documentation (less recommended)

**Files to update:**
- `.cursorrules` (line 17)
- `project-structure.md` (line 10)
- `.claude/instructions.md` (line 17)

### 2.2 CLI Naming Patterns

#### Inconsistent CLI File Naming:
- Most use: `*_cli.py` (e.g., `chunk_headings_cli.py`)
- Exceptions: `new_work__cli.py`, `style_v_hier__cli.py` (double underscore)

**Recommendation:** Standardize to `*_cli.py` pattern:
- `new_work__cli.py` → `new_work_cli.py`
- `style_v_hier__cli.py` → `style_v_hier_cli.py`

### 2.3 Module Export Patterns

#### Inconsistent `__init__.py` Exports:
- Some modules use lazy imports (`__getattr__`) - `chunking/__init__.py`, `vectorization/__init__.py`
- Others use direct imports - `conversions/__init__.py`, `sanitization/__init__.py`
- `retrieval/__init__.py` uses direct imports
- `augmentation/__init__.py` uses direct imports

**Recommendation:** 
- Document the pattern: Use lazy imports for modules with heavy AI dependencies
- Consider standardizing on lazy imports for all modules to improve startup time
- Or standardize on direct imports for simplicity

### 2.4 API Router Naming

#### Consistent Pattern Found:
- All routers follow consistent naming: `routers/{module}.py`
- All schemas follow consistent naming: `schemas/{module}.py`
- ✅ **Good:** This is already standardized

### 2.5 File Structure Standardization

#### Module Organization:
- ✅ **Good:** Consistent `src/psychrag/{module}/` structure
- ✅ **Good:** Consistent `__init__.py` files with exports
- ⚠️ **Issue:** Some modules have README.md files (`conversions/README.md`, `sanitization/README.md`)
- ⚠️ **Issue:** Some modules have markdown prompt files (`conversions/manual_prompt__toc_titles.md`, `conversions/style_v_hier.md`)

**Recommendation:**
- Standardize documentation location (either in module or in `documentation/`)
- Consider moving markdown prompt files to a `prompts/` directory or `documentation/prompts/`

### 2.6 Import Path Standardization

#### Current Patterns:
- API imports: `from psychrag.{module} import {function}`
- Some imports use submodule: `from psychrag.conversions.conv_pdf2md import ...`
- Others use package: `from psychrag.conversions import ...`

**Recommendation:**
- Prefer package-level imports when available: `from psychrag.conversions import convert_pdf_to_markdown`
- Use submodule imports only when necessary (e.g., for internal functions)
- Document preferred import patterns

---

## 3. Code Quality & Documentation

### 3.1 Module Documentation

#### Status:
- ✅ Most CLI modules have docstrings with usage examples
- ✅ API routers have docstrings
- ⚠️ Some library modules lack comprehensive docstrings

**Recommendation:**
- Add module-level docstrings to all library modules
- Include usage examples in docstrings
- Document public API clearly

### 3.2 Type Hints

#### Status:
- ✅ Most functions have type hints
- ⚠️ Some older modules may lack complete type hints

**Recommendation:**
- Run `mypy` or similar tool to identify missing type hints
- Add type hints to all public functions

### 3.3 Error Handling

#### Status:
- ✅ Most API endpoints have proper error handling
- ⚠️ Some CLI modules may have inconsistent error handling

**Recommendation:**
- Standardize error handling patterns
- Use custom exception classes where appropriate
- Document expected exceptions

### 3.4 Testing Coverage

#### Current Test Files:
- `tests/unit/test_api_endpoints.py`
- `tests/unit/test_augment.py`
- `tests/unit/test_conv_epub2md.py`
- `tests/unit/test_conv_pdf2md.py`
- `tests/unit/test_conversion_api_endpoints.py`
- `tests/unit/test_database.py`
- `tests/unit/test_init_db.py`
- `tests/unit/test_inspection.py`
- `tests/unit/test_original_markdown.py`
- `tests/unit/test_prompt_template_model.py`
- `tests/unit/test_templates_api.py`
- `tests/unit/test_work_model.py`

**Recommendation:**
- Run coverage analysis to identify gaps
- Add tests for CLI modules (especially unused ones if keeping them)
- Add integration tests for full workflows
- Document testing strategy

---

## 4. Project Structure Improvements

### 4.1 Configuration Files

#### Current State:
- ✅ `pyproject.toml` - Modern Python packaging
- ✅ `psychrag.config.json` - Application config
- ✅ `.env` - Secrets (should be in `.gitignore`)
- ⚠️ No `requirements.txt` (good - using `pyproject.toml`)

**Recommendation:**
- Add `.env.example` template
- Document all configuration options
- Consider adding `setup.cfg` for tool configuration if needed

### 4.2 Documentation Structure

#### Current State:
- `documentation/` folder exists with various docs
- `README.md` in root
- Module-specific READMEs in some subdirectories

**Recommendation:**
- Organize documentation:
  - `documentation/user-guide/` - User-facing docs
  - `documentation/developer-guide/` - Developer docs
  - `documentation/api/` - API documentation
  - `documentation/cli/` - CLI reference
- Add `CONTRIBUTING.md`
- Add `CHANGELOG.md`
- Add `LICENSE` file (if not present)

### 4.3 Git Configuration

#### Current State:
- `.gitignore` should be present (not checked)
- Git status shows untracked files

**Recommendation:**
- Ensure `.gitignore` includes:
  - `venv/`
  - `__pycache__/`
  - `*.pyc`
  - `.env`
  - `*.egg-info/`
  - IDE-specific files
- Review untracked files and decide what to commit

---

## 5. API Consistency

### 5.1 Endpoint Naming

#### Current Patterns:
- ✅ Consistent use of RESTful patterns
- ✅ Consistent prefix patterns (`/conv/`, `/sanitization/`, `/chunk/`, etc.)
- ✅ Consistent use of HTTP methods

**Status:** ✅ **Good** - API design is consistent

### 5.2 Response Formats

#### Recommendation:
- Document standard response format
- Ensure all endpoints follow consistent error response format
- Consider OpenAPI schema validation

### 5.3 API Versioning

#### Current State:
- No API versioning implemented

**Recommendation:**
- Consider adding API versioning (`/api/v1/`) for future compatibility
- Document versioning strategy

---

## 6. Frontend-Backend Alignment

### 6.1 API Endpoint Usage

#### Analysis:
- UI uses most API endpoints appropriately
- Some endpoints may be underutilized
- Some CLI functionality may need API endpoints

**Recommendation:**
- Review if unused CLI modules should have API endpoints
- Document which operations are CLI-only vs. API-available

### 6.2 Error Handling

#### Recommendation:
- Ensure consistent error handling between frontend and backend
- Document expected error codes and messages
- Add user-friendly error messages

---

## 7. Security Considerations

### 7.1 Secrets Management

#### Current State:
- ✅ Uses `.env` for secrets
- ⚠️ Need to ensure `.env` is in `.gitignore`

**Recommendation:**
- Verify `.env` is gitignored
- Add `.env.example` with placeholder values
- Document required environment variables
- Consider using `python-dotenv` consistently

### 7.2 API Security

#### Recommendation:
- Review CORS configuration
- Consider adding authentication/authorization if needed
- Document security best practices
- Review SQL injection risks (should be handled by SQLAlchemy)

---

## 8. Performance Considerations

### 8.1 Lazy Imports

#### Current State:
- Some modules use lazy imports (`chunking`, `vectorization`)
- Others use direct imports

**Recommendation:**
- Consider expanding lazy imports to all modules with heavy dependencies
- Document the pattern and rationale

### 8.2 Database Queries

#### Recommendation:
- Review for N+1 query problems
- Consider adding query optimization
- Add database indexing documentation

---

## 9. Recommended Action Items

### High Priority (Before Open Source Release)

1. **Fix naming inconsistencies:**
   - Update documentation to use `vectorization/` consistently
   - Standardize CLI file naming (`*_cli.py`)

2. **Clean up unused modules:**
   - Remove or document deprecated CLI modules
   - Decide on CLI-only vs. API-available functionality

3. **Documentation:**
   - Add `CONTRIBUTING.md`
   - Add `LICENSE` file
   - Create comprehensive API documentation
   - Document CLI tools

4. **Testing:**
   - Run coverage analysis
   - Add missing tests
   - Document testing strategy

5. **Configuration:**
   - Add `.env.example`
   - Verify `.gitignore`
   - Document all configuration options

### Medium Priority (Post-Release Improvements)

1. **Standardize import patterns**
2. **Add API versioning**
3. **Expand test coverage**
4. **Performance optimization**
5. **Security audit**

### Low Priority (Nice to Have)

1. **Refactor lazy imports for consistency**
2. **Organize documentation structure**
3. **Add more comprehensive examples**
4. **Create video tutorials**

---

## 10. Module Usage Matrix

### Backend Modules Used by UI (via API)

| Module | CLI File | API Endpoint | Status |
|--------|----------|--------------|--------|
| Conversions | `new_work__cli.py` | `/conv/add-to-database` | ✅ Used |
| Conversions | `style_v_hier__cli.py` | `/conv/suggestion/{file_id}` | ✅ Used |
| Conversions | `conv_pdf2md.py` | `/conv/convert-file` | ✅ Used |
| Conversions | `conv_epub2md.py` | `/conv/convert-file` | ✅ Used |
| Chunking | `chunk_headings_cli.py` | `/chunk/work/{id}/apply-heading-chunks` | ✅ Used |
| Chunking | `content_chunking_cli.py` | `/chunk/work/{id}/apply-content-chunks` | ✅ Used |
| Chunking | `suggested_chunks_cli.py` | `/chunk/work/{id}/vec-suggestions/run` | ✅ Used |
| Sanitization | `extract_titles_cli.py` | `/chunk/work/{id}/extract-sanitized-titles` | ✅ Used |
| Sanitization | `suggest_heading_changes_cli.py` | `/sanitization/work/{id}/prompt` | ✅ Used |
| Sanitization | `apply_title_changes_cli.py` | `/sanitization/work/{id}/apply-title-changes` | ✅ Used |
| Vectorization | `vect_chunks_cli.py` | `/vec/vectorize` | ✅ Used |
| Retrieval | `query_expansion_cli.py` | `/rag/expansion/run` | ✅ Used |
| Retrieval | `query_embeddings_cli.py` | `/rag/queries/{id}/embed` | ✅ Used |
| Retrieval | `retrieve_cli.py` | `/rag/queries/{id}/retrieve` | ✅ Used |
| Augmentation | `consolidate_context_cli.py` | `/rag/queries/{id}/consolidate` | ✅ Used |
| Augmentation | `augment_cli.py` | `/rag/queries/{id}/augment/run` | ✅ Used |
| Data | `db_health_check_cli.py` | `/init/db-health` | ✅ Used |

### Backend Modules NOT Used by UI

| Module | CLI File | Recommendation |
|--------|----------|----------------|
| Chunking | `extract_bib_cli.py` | ⚠️ Remove (deprecated) |
| Chunking | `llm_processor_cli.py` | ⚠️ Review & remove if unused |
| Sanitization | `suggest_heading_from_toc_cli.py` | ⚠️ Review & remove if unused |
| Sanitization | `update_content_hash_cli.py` | ⚠️ Keep for CLI users (internal) |
| Sanitization | `toc_titles2toc_cli.py` | ⚠️ Review & remove if unused |
| Sanitization | `san_map_cli.py` | ⚠️ Review & remove if unused |
| Sanitization | `extract_toc_cli.py` | ⚠️ Review & remove if unused |
| Conversions | `pdf_bookmarks2toc_cli.py` | ⚠️ Review & remove if unused |
| Config | `io_folder_data_cli.py` | ⚠️ Review & remove if unused |
| Utils | `file_utils_cli.py` | ✅ Keep (useful utility) |
| Utils | `model_info_cli.py` | ✅ Keep (debugging tool) |
| Config | `app_config_cli.py` | ✅ Keep (config management) |

---

## 11. Conclusion

The PsychRAG project is well-structured with a clear separation between backend, API, and frontend. The main areas for improvement before open-sourcing are:

1. **Naming consistency** - Fix `vectorizing` vs `vectorization` documentation mismatch
2. **Unused module cleanup** - Remove or document deprecated CLI modules
3. **Documentation** - Add contributing guide, license, and comprehensive API docs
4. **Testing** - Expand test coverage and document testing strategy

The project follows modern Python packaging practices and has a solid foundation. With these improvements, it will be ready for open-source release.

---

## Appendix: File Counts

- **Total CLI modules:** 27
- **CLI modules used by UI:** 18
- **CLI modules not used by UI:** 9
- **API routers:** 9
- **Test files:** 12
- **Documentation files:** Multiple in `documentation/` folder

---

**Next Steps:**
1. Review this document with the team
2. Prioritize action items
3. Create GitHub issues for each improvement
4. Begin implementation based on priority

