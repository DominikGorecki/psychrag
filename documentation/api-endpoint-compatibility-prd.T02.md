# T02 Remove Chunking Router Legacy Tests

## Context

- Link back to the PRD: @documentation/api-endpoint-compatibility-prd.md
- Specific section: **2. Chunking Router Test Removal** (section 2.1)
- The Chunking Router tests include 5 tests for legacy endpoints that don't exist in the current API. The current API uses work-based endpoints (e.g., `/chunk/work/{work_id}/apply-heading-chunks`) rather than file-path-based endpoints. This ticket removes tests for non-existent endpoints to eliminate false negatives.

## Outcome

When this ticket is complete:
- All 5 legacy chunking endpoint tests are removed from the test suite
- Remaining Chunking Router tests (if any) pass correctly
- Test suite no longer contains false negatives for non-existent endpoints
- Test file accurately reflects the actual API implementation

## Scope

- **In scope:**
  - Remove `test_chunk_by_headings()` method
  - Remove `test_chunk_by_content()` method
  - Remove `test_suggest_chunks()` method
  - Remove `test_extract_bibliography()` method
  - Remove `test_process_llm()` method
  - Verify remaining tests pass
  - Verify no syntax errors in test file

- **Out of scope:**
  - Changes to API implementation (API code remains unchanged)
  - Adding tests for actual work-based endpoints (can be done in follow-up ticket)
  - Tests for other routers (handled in T01 and T03)

## Implementation plan

### Test File Updates

1. **Remove `test_chunk_by_headings()` method** in `tests/unit/test_api_endpoints.py`:
   - Delete the entire method (lines 119-128)
   - This endpoint (`POST /chunk/headings`) does not exist in the API
   - Current API uses: `POST /chunk/work/{work_id}/apply-heading-chunks`

2. **Remove `test_chunk_by_content()` method**:
   - Delete the entire method (lines 130-139)
   - This endpoint (`POST /chunk/content`) does not exist in the API
   - Current API uses: `POST /chunk/work/{work_id}/apply-content-chunks`

3. **Remove `test_suggest_chunks()` method**:
   - Delete the entire method (lines 141-149)
   - This endpoint (`POST /chunk/suggest`) does not exist in the API
   - Current API uses: `GET /chunk/work/{work_id}/vec-suggestions/prompt` and related endpoints

4. **Remove `test_extract_bibliography()` method**:
   - Delete the entire method (lines 151-160)
   - This endpoint (`POST /chunk/extract-bib`) does not exist in the API
   - Note: Bibliography extraction may not be implemented in current API

5. **Remove `test_process_llm()` method**:
   - Delete the entire method (lines 162-171)
   - This endpoint (`POST /chunk/process-llm`) does not exist in the API
   - LLM processing may be handled through other endpoints or not exposed via API

6. **Verify `TestChunkingRouter` class structure**:
   - After removals, the class should be empty or contain only valid tests
   - If class becomes empty, consider adding a comment explaining why, or remove the class entirely

### Verification Steps

1. Run Chunking Router tests: `pytest tests/unit/test_api_endpoints.py::TestChunkingRouter -v`
2. Verify no syntax errors
3. Verify remaining tests (if any) pass
4. Run full test suite to ensure no regressions

## Unit tests

Since this ticket removes tests, verify:

- **Test execution:**
  - Run `pytest tests/unit/test_api_endpoints.py::TestChunkingRouter -v`
  - Should show 0 tests (or only valid tests if any remain)
  - No errors or warnings

- **Test file syntax:**
  - Python file parses correctly
  - No indentation errors
  - No missing method definitions

- **Test coverage consideration:**
  - Note that removing these tests may reduce coverage
  - Consider documenting that work-based endpoints may need tests in a future ticket
  - Actual endpoints to potentially test:
    - `GET /chunk/works`
    - `GET /chunk/work/{work_id}`
    - `POST /chunk/work/{work_id}/apply-heading-chunks`
    - `POST /chunk/work/{work_id}/apply-content-chunks`
    - `GET /chunk/work/{work_id}/vec-suggestions/table`
    - And other work-based endpoints

## Dependencies and sequencing

- **No dependencies:** This ticket can be implemented independently
- **Can be done in parallel with:** T01 and T03 (they modify different test classes)
- **Should be done before:** Any future tickets that add tests for Chunking Router endpoints

## Manual test plan

1. **Verify endpoints don't exist:**
   ```bash
   # Try to call the legacy endpoints
   curl -X POST http://localhost:8000/chunk/headings \
     -H "Content-Type: application/json" \
     -d '{"file_path": "/output/test.md", "min_level": 2}'
   
   curl -X POST http://localhost:8000/chunk/content \
     -H "Content-Type: application/json" \
     -d '{"file_path": "/output/test.md", "chunk_size": 512}'
   
   curl -X POST http://localhost:8000/chunk/suggest \
     -H "Content-Type: application/json" \
     -d '{"file_path": "/output/test.md"}'
   
   curl -X POST http://localhost:8000/chunk/extract-bib \
     -H "Content-Type: application/json" \
     -d '{"file_path": "/output/test.md"}'
   
   curl -X POST http://localhost:8000/chunk/process-llm \
     -H "Content-Type: application/json" \
     -d '{"chunk_ids": ["chunk_001"], "operation": "summarize"}'
   ```
   - All should return 404 Not Found

2. **Verify actual endpoints exist (optional):**
   ```bash
   # Check OpenAPI schema
   curl http://localhost:8000/openapi.json | jq '.paths | keys | .[] | select(. | startswith("/chunk"))'
   ```
   - Should show work-based endpoints, not legacy file-path endpoints

3. **Run test suite:**
   ```bash
   venv\Scripts\pytest tests/unit/test_api_endpoints.py::TestChunkingRouter -v
   ```
   - Should show 0 tests (or valid tests only)
   - No errors

## Clarifications and assumptions

### Assumptions
- All 5 endpoints (`/chunk/headings`, `/chunk/content`, `/chunk/suggest`, `/chunk/extract-bib`, `/chunk/process-llm`) do not exist in the API
- The current API uses work-based endpoints as documented in `src/psychrag_api/routers/chunking.py`
- Removing these tests improves test suite reliability by eliminating false negatives

### Open Questions
- **Q1:** Should we add tests for the actual work-based endpoints in this ticket?
  - **Assumption:** No, that's out of scope. Can be done in a follow-up ticket if needed.
- **Q2:** What should happen to the `TestChunkingRouter` class if all tests are removed?
  - **Assumption:** Keep the class structure (even if empty) for consistency, or remove it entirely if it serves no purpose. Adding a comment explaining why it's empty would be helpful.

> **Before implementing:** Verify that all 5 endpoints indeed return 404 by checking the OpenAPI schema (`/openapi.json`) or by making actual API calls. Confirm that the current API uses work-based endpoints as documented.

