COMPLETE

# T001: Remove conversion stub endpoints

## Context

- **PRD**: [cleanup-unused-api-calls.md](cleanup-unused-api-calls.md)
- **PRD Section**: Phase 1: Remove Stub Endpoints (Low Risk) → Ticket 1.1
- **User value**: Reduces technical debt and maintenance burden by removing 4 stub endpoints that were never implemented and are not used by the UI.

## Outcome

The conversion router is cleaned up with 4 stub endpoints removed. The API documentation no longer lists these unimplemented endpoints, and any related test stubs are removed. The codebase is simpler and more maintainable.

## Scope

### In scope
- Remove 4 stub endpoints from `src/psychrag_api/routers/conversion.py`:
  - `GET /conv/formats` (lines 57-86)
  - `POST /conv/epub` (lines 89-119)
  - `POST /conv/pdf` (lines 122-152)
  - `GET /conv/status/{job_id}` (lines 155-178)
- First ensure they aren't used elsewhere, but then remove related response schemas from `src/psychrag_api/schemas/conversion.py`:
  - `SupportedFormatsResponse`
  - `ConversionJobResponse`
  - `ConversionStatusResponse`
- Remove any tests that specifically test these stub endpoints
- Verify no other code references these endpoints or schemas

### Out of scope
- Changes to any other conversion endpoints (all others are in use)
- Changes to other routers (handled in T002-T005)
- UI changes (these endpoints were never integrated)
- Final verification across all removals (handled in T006)

## Implementation plan

### Backend

#### Step 1: Verify schema usage
Before removing schemas, verify they are ONLY used by the endpoints being removed:

```bash
# Search for each schema across the codebase
grep -r "SupportedFormatsResponse" src/
grep -r "ConversionJobResponse" src/
grep -r "ConversionStatusResponse" src/
```

Expected result: Only found in `conversion.py` (router) and `conversion.py` (schema file).

#### Step 2: Remove endpoint handlers from router
File: `src/psychrag_api/routers/conversion.py`

Delete the following functions and their decorators:
- `get_supported_formats()` (lines ~57-86)
- `convert_epub()` (lines ~89-119)
- `convert_pdf()` (lines ~122-152)
- `get_conversion_status()` (lines ~155-178)

The file should go from having these stub endpoints to only having the implemented endpoints that start with `get_io_folder_data_endpoint()`.

#### Step 3: Remove schemas
Ensure they aren't being used elsewhere first.

File: `src/psychrag_api/schemas/conversion.py`

Remove the following Pydantic model classes:
- `SupportedFormatsResponse`
- `ConversionJobResponse`
- `ConversionStatusResponse`

Also remove their imports from the router file if they become unused.

#### Step 4: Update imports
In `src/psychrag_api/routers/conversion.py`, remove the deleted schemas from the import statement at the top:

```python
from psychrag_api.schemas.conversion import (
    # Remove these:
    # ConversionJobResponse,
    # ConversionStatusResponse,
    # SupportedFormatsResponse,
    # Keep the rest...
)
```

### Testing

#### Step 5: Identify and remove stub tests
Check if there are tests for these stub endpoints:

```bash
# Search for tests of the removed endpoints
grep -r "get_supported_formats\|convert_epub\|convert_pdf\|get_conversion_status" tests/
```

If found in `tests/unit/test_conversion_api_endpoints.py`, remove those specific test functions.

#### Step 6: Run test suite
```bash
pytest tests/unit/test_conversion_api_endpoints.py -v
```

Expected: All remaining tests pass. No failures related to missing endpoints.

#### Step 7: Verify API documentation
Start the API server and check the OpenAPI docs:

```bash
uvicorn psychrag_api.main:app --reload
```

Visit http://localhost:8000/docs and verify:
- The 4 removed endpoints no longer appear in the Conversion section
- All other conversion endpoints still appear and work correctly

## Unit tests

### Tests to verify (should still pass)
- Any existing tests for the implemented conversion endpoints should continue passing
- Look for tests in `tests/unit/test_conversion_api_endpoints.py`

### Tests to remove
If any of these test functions exist, remove them:
- `test_get_supported_formats()`
- `test_convert_epub()`
- `test_convert_pdf()`
- `test_get_conversion_status()`

### No new tests needed
Since we're removing unused functionality, no new tests are required. The goal is to ensure existing tests for active endpoints continue to pass.

## Manual test plan

1. **Start the backend**:
   ```bash
   cd c:\code\python\psychRAG-test
   venv\Scripts\activate
   uvicorn psychrag_api.main:app --reload
   ```

2. **Check OpenAPI documentation**:
   - Open http://localhost:8000/docs
   - Navigate to the "Conversion" section
   - Verify these endpoints are GONE:
     - GET /conv/formats
     - POST /conv/epub
     - POST /conv/pdf
     - GET /conv/status/{job_id}
   - Verify these endpoints are STILL PRESENT:
     - GET /conv/io-folder-data
     - POST /conv/convert-file
     - All other conversion endpoints listed in the PRD

3. **Verify UI still works**:
   - Start the UI: `cd psychrag_ui && npm run dev`
   - Navigate to the Conversion page
   - Verify the conversion workflow still functions normally
   - Check browser console for any 404 errors

4. **Run test suite**:
   ```bash
   pytest tests/unit/test_conversion_api_endpoints.py -v
   ```
   Expected: All tests pass, no failures

## Dependencies and sequencing

### Prerequisites
- None - this is the first cleanup ticket and can be done independently

### Blocks
- T006 (Final verification) - should wait for all removal tickets to complete

### Can be done in parallel with
- T002, T003, T004, T005 - all removal tickets are independent

## Clarifications and assumptions

### Assumptions
1. **No CLI usage**: Assuming these stub endpoints are not called by any CLI tools or scripts (per PRD analysis)
2. **Schema isolation**: Assuming the three schemas being removed are only used by these stub endpoints after you ensured they aren't being used elsewhere and if they are, skip removing
3. **Test existence**: Tests for these stubs may or may not exist; will check and remove if found
4. **Single PR acceptable**: All changes can go in one commit/PR since these are unused stubs

### Non-blocking clarifications
- Commit message convention: Should we use a specific format for technical debt cleanup commits?

### Prompt for implementer
> Before implementing, verify the assumptions in the **Clarifications and assumptions** section. Specifically, run the grep commands in Step 1 to confirm the schemas are only used by the endpoints being removed. If you find unexpected usage, stop and consult the team before proceeding with deletion.

## Success criteria

- [x] 4 stub endpoint functions removed from conversion router
- [x] 3 schema classes removed from conversion schemas
- [x] Unused imports cleaned up
- [x] Any stub tests removed
- [ ] All remaining conversion tests pass (manual verification required)
- [ ] OpenAPI docs no longer show the 4 removed endpoints (manual verification required)
- [ ] UI conversion workflow still works normally (manual verification required)
- [ ] No console errors in browser when using conversion features (manual verification required)
