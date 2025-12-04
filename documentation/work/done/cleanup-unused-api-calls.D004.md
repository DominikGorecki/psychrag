COMPLETE

# T004: Remove vec-suggestions content endpoints

## Context

- **PRD**: [cleanup-unused-api-calls.md](cleanup-unused-api-calls.md)
- **PRD Section**: Phase 2: Remove Unused Full Implementations (Medium Risk) → Ticket 2.2
- **User value**: Removes 2 content-based endpoints that were superseded by a more powerful table-based approach. The table endpoints provide richer functionality and are actively used by the UI, making the content endpoints redundant.

## Outcome

The chunking router is cleaned up by removing the superseded content-based vec-suggestions endpoints. Only the modern table-based endpoints remain, simplifying the API surface and reducing maintenance burden.

## Scope

### In scope
- Remove 2 content endpoints from `src/psychrag_api/routers/chunking.py`:
  - `GET /chunk/work/{work_id}/vec-suggestions/content` (lines 435-474)
  - `PUT /chunk/work/{work_id}/vec-suggestions/content` (lines 477-545)
- Remove related schemas from `src/psychrag_api/schemas/chunking.py`:
  - `VecSuggestionsContentResponse`
  - `UpdateVecSuggestionsContentRequest`
- Verify table endpoints remain intact

### Out of scope
- Changes to table-based endpoints (these are actively used):
  - `GET /chunk/work/{work_id}/vec-suggestions/table`
  - `PUT /chunk/work/{work_id}/vec-suggestions/table`
- Changes to other chunking endpoints
- Changes to vec-suggestions business logic (only removing HTTP handlers)
- UI changes (UI uses table endpoints)
- Tests for content endpoints

## Implementation plan

### Backend

#### Step 1: Verify table endpoints are separate
First, confirm the table endpoints are distinct and will not be affected:

```bash
# Find table endpoint definitions
grep -n "vec-suggestions/table" src/psychrag_api/routers/chunking.py
```

Expected: Two separate functions:
- `get_vec_suggestions_table()` around line 785-892
- `update_vec_suggestions_table()` around line 895-990

These should be ABOVE the content endpoints being removed.

#### Step 2: Verify schema usage
Confirm the schemas being removed are ONLY used by the content endpoints:

```bash
# Search for schema usage
grep -r "VecSuggestionsContentResponse" src/
grep -r "UpdateVecSuggestionsContentRequest" src/
```

Expected: Only found in:
- `chunking.py` (router) - in the content endpoint handlers
- `chunking.py` (schema file) - in the schema definitions

Should NOT be found in table endpoints or business logic.

#### Step 3: Remove content endpoint handlers
File: `src/psychrag_api/routers/chunking.py`

Delete these two functions and their decorators:

**Function 1** (lines ~435-474):
```python
@router.get(
    "/work/{work_id}/vec-suggestions/content",
    response_model=VecSuggestionsContentResponse,
    ...
)
async def get_vec_suggestions_content(work_id: int) -> VecSuggestionsContentResponse:
    ...
```

**Function 2** (lines ~477-545):
```python
@router.put(
    "/work/{work_id}/vec-suggestions/content",
    response_model=VecSuggestionsContentResponse,
    ...
)
async def update_vec_suggestions_content(
    work_id: int,
    request: UpdateVecSuggestionsContentRequest
) -> VecSuggestionsContentResponse:
    ...
```

After deletion, the file should jump directly from the san-titles endpoints to the table-based vec-suggestions endpoints.

#### Step 4: Remove schemas
File: `src/psychrag_api/schemas/chunking.py`

Remove these Pydantic model classes:
- `VecSuggestionsContentResponse`
- `UpdateVecSuggestionsContentRequest`

Keep these (used by table endpoints):
- `VecSuggestionRow`
- `VecSuggestionsTableResponse`
- `UpdateVecSuggestionsTableRequest`

#### Step 5: Update imports in router
File: `src/psychrag_api/routers/chunking.py`

Remove the deleted schemas from the import statement:

```python
from psychrag_api.schemas.chunking import (
    # Remove:
    # VecSuggestionsContentResponse,
    # UpdateVecSuggestionsContentRequest,
    # Keep table schemas:
    VecSuggestionRow,
    VecSuggestionsTableResponse,
    UpdateVecSuggestionsTableRequest,
    # ... other schemas ...
)
```

### Testing

#### Step 6: Check for content endpoint tests
Search for tests of the removed content endpoints:

```bash
grep -r "vec-suggestions/content\|get_vec_suggestions_content\|update_vec_suggestions_content" tests/
```

If found in `tests/unit/test_chunking_api_endpoints.py`, remove those specific test functions.

#### Step 7: Verify table endpoint tests remain
Ensure tests for table endpoints are preserved:

```bash
grep -r "vec-suggestions/table" tests/
```

These tests should remain and continue passing.

#### Step 8: Run test suite
```bash
pytest tests/unit/test_chunking_api_endpoints.py -v
```

Expected: Tests for table endpoints pass; content endpoint tests are gone.

#### Step 9: Verify API documentation
```bash
uvicorn psychrag_api.main:app --reload
```

Visit http://localhost:8000/docs → "Chunking" section:
- Verify content endpoints are GONE:
  - GET /chunk/work/{work_id}/vec-suggestions/content
  - PUT /chunk/work/{work_id}/vec-suggestions/content
- Verify table endpoints are PRESENT:
  - GET /chunk/work/{work_id}/vec-suggestions/table
  - PUT /chunk/work/{work_id}/vec-suggestions/table

## Unit tests

### Tests to remove
If these test functions exist, remove them:
- `test_get_vec_suggestions_content()`
- `test_update_vec_suggestions_content()`
- `test_vec_suggestions_content_not_found()`
- Any test specifically testing the `/content` endpoints

### No new tests needed
We're removing superseded functionality.

## Manual test plan

1. **Start the backend**:
   ```bash
   cd c:\code\python\psychRAG-test
   venv\Scripts\activate
   uvicorn psychrag_api.main:app --reload
   ```

2. **Check OpenAPI documentation**:
   - Open http://localhost:8000/docs
   - Navigate to "Chunking" section
   - Scroll to vec-suggestions endpoints
   - Verify content endpoints are GONE:
     - ❌ GET /chunk/work/{work_id}/vec-suggestions/content
     - ❌ PUT /chunk/work/{work_id}/vec-suggestions/content
   - Verify table endpoints are PRESENT:
     - ✅ GET /chunk/work/{work_id}/vec-suggestions/table
     - ✅ PUT /chunk/work/{work_id}/vec-suggestions/table
   - Verify other vec-suggestions endpoints remain:
     - GET /chunk/work/{work_id}/vec-suggestions/prompt
     - POST /chunk/work/{work_id}/vec-suggestions/manual
     - POST /chunk/work/{work_id}/vec-suggestions/run

3. **Verify UI chunking workflow with vec-suggestions**:
   - Start UI: `cd psychrag_ui && npm run dev`
   - Navigate to Chunking page
   - Select a work with sanitized content
   - Navigate to vec-suggestions page for that work
   - Verify the interactive table loads and works:
     - Table displays all headings
     - Can edit vectorization decisions
     - Can save changes
   - Check browser console for errors
   - Per PRD, UI uses `/table` endpoints at:
     - `chunk/[id]/vec-suggestions/page.tsx:93` (GET)
     - `chunk/[id]/vec-suggestions/page.tsx:131` (PUT)

4. **Run test suite**:
   ```bash
   pytest tests/unit/test_chunking_api_endpoints.py -v
   ```
   Expected: All table-based tests pass

## Dependencies and sequencing

### Prerequisites
- None - can be done independently

### Blocks
- T006 (Final verification) - should wait for all removal tickets

### Can be done in parallel with
- T001, T002, T003, T005 - all independent

## Clarifications and assumptions

### Assumptions
1. **Table supersedes content**: The table endpoints provide all functionality of content endpoints plus interactive editing (per PRD)
2. **UI never used content**: The UI was built directly against table endpoints (verified in PRD with line number references)
3. **No CLI usage**: No CLI scripts use the content endpoints
4. **Business logic shared**: The underlying business logic is shared between content and table endpoints, so only HTTP handlers need removal

### Non-blocking clarifications
- **Migration path**: If we ever need to restore raw content access, we can add it back using the business logic that remains (just remove HTTP layer)

### Prompt for implementer
> Before implementing, verify in Step 1 that the table endpoints are indeed separate functions and will not be affected by removing the content endpoints. The table endpoints should be defined AFTER the content endpoints in the file. If the structure is different than expected, review the file carefully before proceeding with deletion.

## Success criteria

- [ ] 2 content endpoint handlers removed from chunking router
- [ ] 2 schema classes removed from chunking schemas
- [ ] Unused imports cleaned up
- [ ] Any content endpoint tests removed
- [ ] All table endpoint tests pass
- [ ] OpenAPI docs show only table endpoints for vec-suggestions
- [ ] UI vec-suggestions page works normally with table interface
- [ ] No console errors when using vec-suggestions feature
- [ ] Other chunking endpoints unaffected
