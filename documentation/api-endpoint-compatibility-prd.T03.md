# T03 Remove RAG Router Legacy Tests

## Context

- Link back to the PRD: @documentation/api-endpoint-compatibility-prd.md
- Specific section: **3. RAG Router Test Removal** (section 3.1)
- The RAG Router tests include 5 tests for legacy endpoints that don't exist in the current API. The current API uses query-based endpoints (e.g., `/rag/queries`, `/rag/expansion/run`) rather than simple action endpoints. This ticket removes tests for non-existent endpoints to eliminate false negatives.

## Outcome

When this ticket is complete:
- All 5 legacy RAG endpoint tests are removed from the test suite
- Remaining RAG Router tests (if any) pass correctly
- Test suite no longer contains false negatives for non-existent endpoints
- Test file accurately reflects the actual API implementation

## Scope

- **In scope:**
  - Remove `test_rag_query()` method
  - Remove `test_retrieve_chunks()` method
  - Remove `test_expand_query()` method
  - Remove `test_augment_content()` method
  - Remove `test_generate_response()` method
  - Verify remaining tests pass
  - Verify no syntax errors in test file

- **Out of scope:**
  - Changes to API implementation (API code remains unchanged)
  - Adding tests for actual query-based endpoints (can be done in follow-up ticket)
  - Tests for other routers (handled in T01 and T02)

## Implementation plan

### Test File Updates

1. **Remove `test_rag_query()` method** in `tests/unit/test_api_endpoints.py`:
   - Delete the entire method (lines 221-231)
   - This endpoint (`POST /rag/query`) does not exist in the API
   - Current API uses query-based workflow: create query, then run operations

2. **Remove `test_retrieve_chunks()` method**:
   - Delete the entire method (lines 233-242)
   - This endpoint (`POST /rag/retrieve`) does not exist in the API
   - Current API uses: `POST /rag/queries/{id}/retrieve` (requires query ID)

3. **Remove `test_expand_query()` method**:
   - Delete the entire method (lines 244-254)
   - This endpoint (`POST /rag/expand-query`) does not exist in the API
   - Current API uses: `POST /rag/expansion/prompt` and `POST /rag/expansion/run`

4. **Remove `test_augment_content()` method**:
   - Delete the entire method (lines 256-265)
   - This endpoint (`POST /rag/augment`) does not exist in the API
   - Current API uses: `GET /rag/queries/{id}/augment/prompt` and related endpoints

5. **Remove `test_generate_response()` method**:
   - Delete the entire method (lines 267-279)
   - This endpoint (`POST /rag/generate`) does not exist in the API
   - Response generation may be handled through query-based endpoints or not exposed via API

6. **Verify `TestRAGRouter` class structure**:
   - After removals, the class should be empty or contain only valid tests
   - If class becomes empty, consider adding a comment explaining why, or remove the class entirely

### Verification Steps

1. Run RAG Router tests: `pytest tests/unit/test_api_endpoints.py::TestRAGRouter -v`
2. Verify no syntax errors
3. Verify remaining tests (if any) pass
4. Run full test suite to ensure no regressions

## Unit tests

Since this ticket removes tests, verify:

- **Test execution:**
  - Run `pytest tests/unit/test_api_endpoints.py::TestRAGRouter -v`
  - Should show 0 tests (or only valid tests if any remain)
  - No errors or warnings

- **Test file syntax:**
  - Python file parses correctly
  - No indentation errors
  - No missing method definitions

- **Test coverage consideration:**
  - Note that removing these tests may reduce coverage
  - Consider documenting that query-based endpoints may need tests in a future ticket
  - Actual endpoints to potentially test:
    - `GET /rag/queries`
    - `GET /rag/queries/{id}`
    - `POST /rag/queries/{id}/embed`
    - `POST /rag/queries/{id}/retrieve`
    - `POST /rag/queries/{id}/consolidate`
    - `POST /rag/expansion/prompt`
    - `POST /rag/expansion/run`
    - `POST /rag/expansion/manual`
    - And other query-based endpoints

## Dependencies and sequencing

- **No dependencies:** This ticket can be implemented independently
- **Can be done in parallel with:** T01 and T02 (they modify different test classes)
- **Should be done before:** Any future tickets that add tests for RAG Router endpoints

## Manual test plan

1. **Verify endpoints don't exist:**
   ```bash
   # Try to call the legacy endpoints
   curl -X POST http://localhost:8000/rag/query \
     -H "Content-Type: application/json" \
     -d '{"query": "What is cognitive load theory?"}'
   
   curl -X POST http://localhost:8000/rag/retrieve \
     -H "Content-Type: application/json" \
     -d '{"query": "working memory", "top_k": 5}'
   
   curl -X POST http://localhost:8000/rag/expand-query \
     -H "Content-Type: application/json" \
     -d '{"query": "cognitive load"}'
   
   curl -X POST http://localhost:8000/rag/augment \
     -H "Content-Type: application/json" \
     -d '{"content": "Cognitive load refers to..."}'
   
   curl -X POST http://localhost:8000/rag/generate \
     -H "Content-Type: application/json" \
     -d '{"query": "Summarize memory", "context_chunks": ["chunk_001", "chunk_002"]}'
   ```
   - All should return 404 Not Found

2. **Verify actual endpoints exist (optional):**
   ```bash
   # Check OpenAPI schema
   curl http://localhost:8000/openapi.json | jq '.paths | keys | .[] | select(. | startswith("/rag"))'
   ```
   - Should show query-based endpoints, not legacy action endpoints

3. **Run test suite:**
   ```bash
   venv\Scripts\pytest tests/unit/test_api_endpoints.py::TestRAGRouter -v
   ```
   - Should show 0 tests (or valid tests only)
   - No errors

## Clarifications and assumptions

### Assumptions
- All 5 endpoints (`/rag/query`, `/rag/retrieve`, `/rag/expand-query`, `/rag/augment`, `/rag/generate`) do not exist in the API
- The current API uses query-based endpoints as documented in `src/psychrag_api/routers/rag.py`
- Removing these tests improves test suite reliability by eliminating false negatives
- The query-based workflow (create query → run operations) is the correct API design

### Open Questions
- **Q1:** Should we add tests for the actual query-based endpoints in this ticket?
  - **Assumption:** No, that's out of scope. Can be done in a follow-up ticket if needed.
- **Q2:** What should happen to the `TestRAGRouter` class if all tests are removed?
  - **Assumption:** Keep the class structure (even if empty) for consistency, or remove it entirely if it serves no purpose. Adding a comment explaining why it's empty would be helpful.

> **Before implementing:** Verify that all 5 endpoints indeed return 404 by checking the OpenAPI schema (`/openapi.json`) or by making actual API calls. Confirm that the current API uses query-based endpoints as documented in the router implementation.

