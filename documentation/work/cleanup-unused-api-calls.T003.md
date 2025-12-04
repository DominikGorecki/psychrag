COMPLETE

# T003: Remove verify-title-changes endpoint

## Context

- **PRD**: [cleanup-unused-api-calls.md](cleanup-unused-api-calls.md)
- **PRD Section**: Phase 2: Remove Unused Full Implementations (Medium Risk) → Ticket 2.1
- **User value**: Removes a fully implemented but never integrated endpoint that adds maintenance burden. This endpoint validates title changes file integrity but was never exposed to users through the UI workflow.

## Outcome

The `verify-title-changes` endpoint is completely removed from the sanitization API along with its business logic implementation. The codebase is simpler without this unused validation feature.

## Scope

### In scope
- Remove endpoint handler from `src/psychrag_api/routers/sanitization.py`:
  - `POST /sanitization/work/{work_id}/verify-title-changes` (lines 419-460)
- Remove schemas from `src/psychrag_api/schemas/sanitization.py`:
  - `VerifyTitleChangesRequest`
  - `VerifyTitleChangesResponse`
- Remove business logic function:
  - `verify_title_changes_integrity()` from `src/psychrag/sanitization/`
- Remove the function export from `src/psychrag/sanitization/__init__.py`
- Remove any tests specifically for this endpoint

### Out of scope
- Changes to other sanitization endpoints (all in active use)
- Changes to title changes workflow (this verification was never part of it)
- UI changes (endpoint was never integrated)
- Running the tests -- I will run them manually

## Implementation plan

### Backend

#### Step 1: Locate and verify business logic function
First, find where the business logic is implemented:

```bash
# Search for the function definition
grep -r "def verify_title_changes_integrity" src/psychrag/sanitization/
```

Expected locations:
- Either in a dedicated file: `src/psychrag/sanitization/verify_title_changes.py`
- Or in an existing file like `src/psychrag/sanitization/__init__.py` or similar

Take note of the file path for later deletion.

#### Step 2: Check function dependencies
Verify that `verify_title_changes_integrity()` is ONLY called by the endpoint being removed:

```bash
# Search for all usages of the function
grep -r "verify_title_changes_integrity" src/
```

Expected result: Only found in:
1. The function definition itself
2. The endpoint handler in `sanitization.py` (router)
3. The export in `__init__.py`
4. Possibly in tests

If found elsewhere, **STOP** and consult the team - this indicates the function is used by other code.

#### Step 3: Remove endpoint handler
File: `src/psychrag_api/routers/sanitization.py`

Delete the `verify_title_changes()` endpoint function and its decorator (lines ~419-460):

```python
@router.post(
    "/work/{work_id}/verify-title-changes",
    ...
)
async def verify_title_changes(
    work_id: int,
    request: VerifyTitleChangesRequest
) -> VerifyTitleChangesResponse:
    ...
```

#### Step 4: Remove schemas
File: `src/psychrag_api/schemas/sanitization.py`

Remove these Pydantic model classes:
- `VerifyTitleChangesRequest`
- `VerifyTitleChangesResponse`

#### Step 5: Remove business logic function
Based on what you found in Step 1, remove the function definition:

**Option A**: If in a dedicated file `verify_title_changes.py`:
```bash
# Delete the entire file
rm src/psychrag/sanitization/verify_title_changes.py
```

**Option B**: If in an existing file:
- Open the file and delete only the `verify_title_changes_integrity()` function definition
- Keep all other functions in the file

#### Step 6: Update __init__.py
File: `src/psychrag/sanitization/__init__.py`

Remove the export of `verify_title_changes_integrity`:

```python
# Remove this line:
from .verify_title_changes import verify_title_changes_integrity

# Or remove from __all__ list:
__all__ = [
    # ... other exports ...
    # "verify_title_changes_integrity",  # Remove this
]
```

#### Step 7: Update imports in router
File: `src/psychrag_api/routers/sanitization.py`

Remove the import of the deleted function and schemas:

```python
from psychrag.sanitization import (
    # Remove:
    # verify_title_changes_integrity,
    # Keep other imports...
)

from psychrag_api.schemas.sanitization import (
    # Remove:
    # VerifyTitleChangesRequest,
    # VerifyTitleChangesResponse,
    # Keep other schemas...
)
```

### Testing

#### Step 8: Find and remove tests
Search for tests of the verify endpoint:

```bash
grep -r "verify_title_changes" tests/
```

Likely locations:
- `tests/unit/test_sanitization_api_endpoints.py` - for endpoint tests
- `tests/unit/test_sanitization.py` or similar - for business logic tests

Remove test functions like:
- `test_verify_title_changes()`
- `test_verify_title_changes_integrity()`
- Any tests with "verify" in the name related to title changes

## Unit tests

### Tests to remove
Remove any tests that specifically test the verify functionality:

**From endpoint tests** (`test_sanitization_api_endpoints.py`):
- `test_verify_title_changes_success()`
- `test_verify_title_changes_integrity_error()`
- Any test calling the `/verify-title-changes` endpoint

**From business logic tests**:
- `test_verify_title_changes_integrity()`
- `test_verify_detects_missing_titles()`
- `test_verify_detects_hash_mismatch()`
- Any test calling `verify_title_changes_integrity()`

### No new tests needed
We're removing unused functionality.

## Manual test plan

1. **Start the backend**:
   ```bash
   cd c:\code\python\psychRAG-test
   venv\Scripts\activate
   uvicorn psychrag_api.main:app --reload
   ```

2. **Check OpenAPI documentation**:
   - Open http://localhost:8000/docs
   - Navigate to "Sanitization" section
   - Verify `POST /sanitization/work/{work_id}/verify-title-changes` is GONE
   - Verify these endpoints are STILL PRESENT:
     - POST /sanitization/work/{work_id}/extract-titles
     - POST /sanitization/work/{work_id}/suggest-title-changes
     - POST /sanitization/work/{work_id}/apply-title-changes
     - All other sanitization endpoints

3. **Verify UI sanitization workflow**:
   - Start UI: `cd psychrag_ui && npm run dev`
   - Navigate to Sanitization page
   - Run through complete sanitization workflow for a work:
     1. Extract titles
     2. Generate title changes
     3. Review/edit title changes
     4. Apply title changes
   - Verify no errors or console warnings
   - The workflow should work identically to before (since verify was never integrated)

4. **Run full test suite**:
   ```bash
   pytest tests/unit/test_sanitization*.py -v
   ```
   Expected: All tests pass

## Dependencies and sequencing

### Prerequisites
- None - can be done independently

### Blocks
- T006 (Final verification) - should wait for all removal tickets

### Can be done in parallel with
- T001, T002, T004, T005 - all independent

## Clarifications and assumptions

### Assumptions
1. **No integration**: The verify endpoint was truly never integrated into any UI workflow (per PRD analysis)
2. **Function isolation**: `verify_title_changes_integrity()` is only called by the endpoint being removed
3. **No CLI usage**: No CLI scripts call this verification function
4. **HashMismatchError preserved**: The `HashMismatchError` exception class is used by other functions and should NOT be removed even if imported by the verify function

### Blocking clarifications
- **Function location**: If the grep in Step 1 shows the function in an unexpected location or if there are multiple implementations, clarify which one to remove
- **Unexpected dependencies**: If Step 2 shows the function is called from places other than the endpoint, **DO NOT PROCEED** until clarifying with the team

### Non-blocking clarifications
- Git history: Should we add a note in the commit message about why this fully-implemented feature is being removed?

### Prompt for implementer
> Before implementing, complete Steps 1-2 to verify the function location and ensure it has no dependencies outside the endpoint being removed. If you find the function is called from other places (CLI, other endpoints, background jobs), STOP and consult the team before deleting. This is a fully-implemented feature, so we need to be certain it's truly unused before removal.

## Success criteria

- [ ] Endpoint handler removed from sanitization router
- [ ] Two schema classes removed
- [ ] Business logic function removed (file deleted or function removed from shared file)
- [ ] Function export removed from `__init__.py`
- [ ] All imports cleaned up
- [ ] All verify-related tests removed
- [ ] All other sanitization tests pass
- [ ] OpenAPI docs don't show verify endpoint
- [ ] UI sanitization workflow works normally
- [ ] No console errors
- [ ] Grep confirms function is completely gone from codebase
