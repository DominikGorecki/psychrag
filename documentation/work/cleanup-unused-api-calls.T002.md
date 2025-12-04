# T002: Remove sanitization legacy stub endpoints

## Context

- **PRD**: [cleanup-unused-api-calls.md](cleanup-unused-api-calls.md)
- **PRD Section**: Phase 1: Remove Stub Endpoints (Low Risk) → Ticket 1.2
- **User value**: Removes 4 legacy stub endpoints that were superseded by the new work-based sanitization API. Simplifies the sanitization router and removes confusion between old and new endpoint patterns.

## Outcome

The sanitization router is cleaned up with 4 legacy stub endpoints removed. The API now only exposes the modern work-based sanitization endpoints. Related legacy schemas are removed while preserving the newer work-based schemas.

## Scope

### In scope
- Remove 4 legacy stub endpoints from `src/psychrag_api/routers/sanitization.py`:
  - `POST /sanitization/extract-toc` (lines 963-984)
  - `POST /sanitization/extract-titles` (lines 987-1006)
  - `POST /sanitization/suggest-changes` (lines 1009-1033)
  - `POST /sanitization/apply-changes` (lines 1036-1055)
- Remove legacy schemas from `src/psychrag_api/schemas/sanitization.py`:
  - `ExtractTOCRequest`
  - `ExtractTOCResponse`
  - Legacy `ExtractTitlesRequest` (NOT the work-based version)
  - Legacy `ExtractTitlesResponse` (NOT the work-based version)
  - `SuggestChangesRequest`
  - `SuggestChangesResponse`
  - `ApplyChangesRequest`
  - `ApplyChangesResponse`
- Keep all work-based schemas (those used by `/work/{work_id}/*` endpoints)

### Out of scope
- Changes to work-based sanitization endpoints (all in active use)
- Removal of verify-title-changes endpoint (handled in T003)
- Changes to other routers (handled in T001, T004, T005)
- UI changes (legacy endpoints were never integrated)

## Implementation plan

### Backend

#### Step 1: Identify legacy vs work-based schemas
File: `src/psychrag_api/schemas/sanitization.py`

Carefully distinguish between:
- **Legacy schemas to REMOVE**: Used only by the 4 stub endpoints
- **Work-based schemas to KEEP**: Used by active `/work/{work_id}/*` endpoints

Create a checklist:
```
Remove:
- ExtractTOCRequest
- ExtractTOCResponse
- ExtractTitlesRequest (legacy - check if it's different from work-based version)
- ExtractTitlesResponse (legacy)
- SuggestChangesRequest
- SuggestChangesResponse
- ApplyChangesRequest
- ApplyChangesResponse

Keep:
- ExtractTitlesFromWorkRequest (work-based)
- ExtractTitlesFromWorkResponse (work-based)
- SuggestTitleChangesRequest (work-based)
- SuggestTitleChangesResponse (work-based)
- ApplyTitleChangesRequest (work-based)
- ApplyTitleChangesResponse (work-based)
- All other work-based schemas
```

#### Step 2: Verify schema usage
Search for each legacy schema to confirm it's only used by the stub endpoints:

```bash
grep -r "ExtractTOCRequest\|ExtractTOCResponse" src/
grep -r "SuggestChangesRequest\|SuggestChangesResponse" src/
grep -r "ApplyChangesRequest\|ApplyChangesResponse" src/
```

Expected: Only found in sanitization router and schema file.

#### Step 3: Remove legacy endpoint handlers
File: `src/psychrag_api/routers/sanitization.py`

Delete the following functions (at the end of the file, marked with "Legacy endpoints"):
- `extract_toc()` (lines ~963-984)
- `extract_titles()` (lines ~987-1006) - Note: This is the legacy version, NOT `extract_titles_from_work_endpoint()`
- `suggest_changes()` (lines ~1009-1033)
- `apply_changes()` (lines ~1036-1055)

Look for the comment `# Legacy endpoints (kept for backwards compatibility)` around line 961 - remove everything from that comment onward.

#### Step 4: Remove legacy schemas
File: `src/psychrag_api/schemas/sanitization.py`

Remove the legacy schema classes identified in Step 1. Be careful to:
- NOT remove work-based schemas with similar names
- Check if there are any base classes or mixins that become unused

#### Step 5: Update imports
In `src/psychrag_api/routers/sanitization.py`, remove the deleted legacy schemas from the import statement:

```python
from psychrag_api.schemas.sanitization import (
    # Remove legacy schemas:
    # ApplyChangesRequest,
    # ApplyChangesResponse,
    # ExtractTitlesRequest,
    # ExtractTitlesResponse,
    # ExtractTOCRequest,
    # ExtractTOCResponse,
    # SuggestChangesRequest,
    # SuggestChangesResponse,
    # Keep all work-based schemas...
)
```

### Testing

#### Step 6: Identify and remove legacy stub tests
Check for tests of the legacy endpoints:

```bash
grep -r "extract_toc\|extract_titles\|suggest_changes\|apply_changes" tests/unit/test_sanitization*
```

If found, remove test functions that specifically test the removed legacy endpoints. Be careful NOT to remove tests for work-based endpoints with similar names.

#### Step 7: Run test suite
```bash
pytest tests/unit/test_sanitization_api_endpoints.py -v
```

Expected: All work-based sanitization tests pass.

#### Step 8: Verify API documentation
```bash
uvicorn psychrag_api.main:app --reload
```

Visit http://localhost:8000/docs → "Sanitization" section:
- Verify the 4 legacy endpoints are gone
- Verify all `/sanitization/work/{work_id}/*` endpoints remain

## Unit tests

### Tests to verify (should still pass)
- All tests for work-based sanitization endpoints in `tests/unit/test_sanitization_api_endpoints.py`
- Tests like:
  - `test_extract_titles_from_work()`
  - `test_suggest_title_changes()`
  - `test_apply_title_changes()`
  - Any tests following the `/work/{work_id}/*` pattern

### Tests to remove
If any of these legacy test functions exist, remove them:
- `test_extract_toc()` (legacy version)
- `test_extract_titles()` (legacy version, NOT work-based version)
- `test_suggest_changes()` (legacy version)
- `test_apply_changes()` (legacy version)

Look for tests that DON'T include `work_id` in their setup - those are likely legacy tests.

### No new tests needed
We're removing unused functionality, so no new tests are required.

## Manual test plan

1. **Start the backend**:
   ```bash
   cd c:\code\python\psychRAG-test
   venv\Scripts\activate
   uvicorn psychrag_api.main:app --reload
   ```

2. **Check OpenAPI documentation**:
   - Open http://localhost:8000/docs
   - Navigate to the "Sanitization" section
   - Verify these legacy endpoints are GONE:
     - POST /sanitization/extract-toc
     - POST /sanitization/extract-titles
     - POST /sanitization/suggest-changes
     - POST /sanitization/apply-changes
   - Verify these work-based endpoints are STILL PRESENT:
     - GET /sanitization/works
     - POST /sanitization/work/{work_id}/extract-titles
     - POST /sanitization/work/{work_id}/suggest-title-changes
     - POST /sanitization/work/{work_id}/apply-title-changes
     - All other `/work/{work_id}/*` endpoints

3. **Verify UI sanitization workflow**:
   - Start UI: `cd psychrag_ui && npm run dev`
   - Navigate to Sanitization page
   - Select a work and run through the sanitization workflow:
     - Extract titles
     - Suggest title changes
     - Apply title changes
   - Verify no console errors

4. **Run test suite**:
   ```bash
   pytest tests/unit/test_sanitization_api_endpoints.py -v
   ```
   Expected: All work-based tests pass

## Dependencies and sequencing

### Prerequisites
- None - can be done independently of other tickets

### Blocks
- T006 (Final verification) - should wait for all removal tickets

### Can be done in parallel with
- T001, T003, T004, T005 - all removal tickets are independent

## Clarifications and assumptions

### Assumptions
1. **Legacy vs work-based distinction**: The schemas can be clearly distinguished by naming convention (legacy = simple names, work-based = includes "FromWork" or "Work" in name)
2. **No CLI usage**: Legacy endpoints are not called by CLI tools (per PRD)
3. **Comment marker exists**: The "Legacy endpoints" comment section exists around line 961 in sanitization.py
4. **Test naming**: Legacy tests (if they exist) don't include `work_id` in their setup

### Blocking clarifications
- **Schema disambiguation**: If there are schemas with identical names for legacy and work-based versions, we need to determine which is which before deletion

### Prompt for implementer
> Before implementing, carefully review Step 1 to distinguish legacy schemas from work-based schemas. If there's any ambiguity about which schema is which, check the usage in the router file to confirm which schemas are used by the legacy stub endpoints vs the work-based endpoints. Only remove schemas used exclusively by the 4 legacy stubs.

## Success criteria

- [ ] 4 legacy stub endpoint functions removed from sanitization router
- [ ] 8 legacy schema classes removed from sanitization schemas
- [ ] All work-based schemas preserved
- [ ] Unused imports cleaned up
- [ ] Any legacy stub tests removed
- [ ] All work-based sanitization tests pass
- [ ] OpenAPI docs show work-based endpoints only
- [ ] UI sanitization workflow still works normally
- [ ] No console errors when using sanitization features
