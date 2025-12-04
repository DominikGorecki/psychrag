# T005: Remove chunks/count debug endpoint

## Context

- **PRD**: [cleanup-unused-api-calls.md](cleanup-unused-api-calls.md)
- **PRD Section**: Phase 2: Remove Unused Full Implementations (Medium Risk) → Ticket 2.3
- **User value**: Removes a debug endpoint that was never integrated into the UI. This endpoint was likely created during development for debugging purposes but is not needed in production.

## Outcome

The chunking router is cleaned up by removing the debug chunks count endpoint. The API surface is simplified by removing this internal debugging tool that provides no user-facing value.

## Scope

### In scope
- Remove debug endpoint from `src/psychrag_api/routers/chunking.py`:
  - `GET /chunk/work/{work_id}/chunks/count` (lines 624-645)
- No schema removal needed (returns plain dict)
- Verify no tests depend on this endpoint

### Out of scope
- Changes to other chunking endpoints (all in active use)
- Changes to chunk data models or business logic
- UI changes (endpoint was never integrated)

## Implementation plan

### Backend

#### Step 1: Verify endpoint is truly a debug tool
Review the endpoint implementation to confirm it's debug-only:

File: `src/psychrag_api/routers/chunking.py` (around lines 624-645)

Expected characteristics:
- Returns simple count and database info
- Includes comment "for debugging"
- Returns masked database URL
- No complex business logic
- No schema definition (returns plain dict)

#### Step 2: Check for any dependencies
Verify the endpoint is not called from anywhere:

```bash
# Search for any usage of the endpoint
grep -r "chunks/count" src/ psychrag_ui/
grep -r "get_chunk_count" src/
```

Expected result: Only found in the chunking router definition itself.

#### Step 3: Remove the endpoint handler
File: `src/psychrag_api/routers/chunking.py`

Delete the entire function and its decorator (lines ~624-645):

```python
@router.get(
    "/work/{work_id}/chunks/count",
    summary="Get chunk count for work",
    description="Returns the number of chunks for this work (for debugging).",
)
async def get_chunk_count(work_id: int) -> dict:
    """Get chunk count for debugging."""
    from psychrag.data.database import get_database_url
    with get_session() as session:
        from psychrag.data.models import Chunk

        count = session.query(Chunk).filter(Chunk.work_id == work_id).count()

        # Get database info (mask password)
        db_url = get_database_url()
        db_url_safe = db_url.split('@')[1] if '@' in db_url else db_url

        return {
            "work_id": work_id,
            "chunk_count": count,
            "database": db_url_safe
        }
```

After deletion, the file should go directly from the `apply_content_chunks` function to the `get_vec_suggestions_prompt` function (or whichever function follows).

#### Step 4: Verify no imports need cleanup
Check if any imports were used exclusively by this endpoint:

The endpoint imports:
- `get_database_url` from `psychrag.data.database`
- `Chunk` from `psychrag.data.models`

Verify these imports are used by other functions in the file:

```bash
# Check if get_database_url is used elsewhere in the file
grep "get_database_url" src/psychrag_api/routers/chunking.py

# Check if Chunk is used elsewhere
grep "Chunk" src/psychrag_api/routers/chunking.py
```

If these imports are ONLY in the removed function:
- The imports are inside the function, so no cleanup needed at the file level

### Testing

#### Step 5: Check for tests of the debug endpoint
Search for any tests:

```bash
grep -r "chunks/count\|get_chunk_count" tests/
```

If found in `tests/unit/test_chunking_api_endpoints.py`, remove that test function.

#### Step 6: Run test suite
```bash
pytest tests/unit/test_chunking_api_endpoints.py -v
```

Expected: All remaining chunking tests pass.

#### Step 7: Verify API documentation
```bash
uvicorn psychrag_api.main:app --reload
```

Visit http://localhost:8000/docs → "Chunking" section:
- Verify `GET /chunk/work/{work_id}/chunks/count` is gone
- Verify all other chunking endpoints remain

## Unit tests

### Tests to remove
If this test function exists, remove it:
- `test_get_chunk_count()`
- `test_chunks_count_endpoint()`
- Any test specifically testing the `/chunks/count` endpoint

### Tests to verify still pass
All other chunking endpoint tests should pass:
- Tests for work listing
- Tests for heading chunks
- Tests for content chunks
- Tests for vec-suggestions
- Tests for sanitized content

### No new tests needed
We're removing a debug endpoint.

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
   - Verify `GET /chunk/work/{work_id}/chunks/count` is GONE
   - Verify all other chunking endpoints are PRESENT:
     - GET /chunk/works
     - GET /chunk/work/{work_id}
     - POST /chunk/work/{work_id}/apply-heading-chunks
     - POST /chunk/work/{work_id}/apply-content-chunks
     - All other chunking endpoints

3. **Verify UI chunking workflow**:
   - Start UI: `cd psychrag_ui && npm run dev`
   - Navigate to Chunking page
   - Select a work and run through chunking workflow:
     - Extract sanitized titles
     - Generate vec suggestions
     - Apply heading chunks
     - Apply content chunks
   - Verify no console errors
   - Per PRD, the debug endpoint was never used by UI

4. **Run test suite**:
   ```bash
   pytest tests/unit/test_chunking_api_endpoints.py -v
   ```
   Expected: All tests pass

5. **Optional: Verify chunk counts still accessible via database**:
   If needed for debugging in the future, developers can still query chunk counts directly:
   ```python
   from psychrag.data.database import get_session
   from psychrag.data.models import Chunk

   with get_session() as session:
       count = session.query(Chunk).filter(Chunk.work_id == work_id).count()
   ```

## Dependencies and sequencing

### Prerequisites
- None - can be done independently

### Blocks
- T006 (Final verification) - should wait for all removal tickets

### Can be done in parallel with
- T001, T002, T003, T004 - all independent

## Clarifications and assumptions

### Assumptions
1. **Debug-only purpose**: This endpoint was created for development/debugging and has no production use case
2. **No UI integration**: The endpoint was never integrated into any UI page (per PRD analysis showing no fetch calls)
3. **No CLI usage**: No CLI scripts depend on this endpoint for monitoring or debugging
4. **Database access remains**: Developers can still query chunk counts directly via the database if needed for debugging

### Non-blocking clarifications
- **Alternative debugging**: Should we document how to query chunk counts directly via database for future debugging needs?
- **Monitoring concerns**: Are there any monitoring or alerting systems that might be calling this endpoint? (Unlikely since it's a debug endpoint with work_id parameter)

### Prompt for implementer
> Before implementing, verify in Step 2 that the endpoint is truly not used anywhere in the codebase or UI. This is a straightforward removal since it's a simple debug endpoint, but it's always good to double-check. If you find any unexpected usage, stop and consult the team.

## Success criteria

- [ ] Debug endpoint handler removed from chunking router
- [ ] No schema removal needed (endpoint returned plain dict)
- [ ] No import cleanup needed (imports were inside the function)
- [ ] Any debug endpoint test removed
- [ ] All other chunking tests pass
- [ ] OpenAPI docs don't show the debug endpoint
- [ ] UI chunking workflow works normally
- [ ] No console errors
- [ ] Other chunking endpoints unaffected
