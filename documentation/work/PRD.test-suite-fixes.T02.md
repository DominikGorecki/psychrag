COMPLETE

# T02: Fix Async Test Support (16 tests)

## Context

- **PRD**: [PRD.test-suite-fixes.md](PRD.test-suite-fixes.md)
- **PRD Section**: Phase 2: Async Test Support (Section 5.1, FR2.1-FR2.3)
- This ticket fixes 16 failing tests across 2 test modules that are failing due to missing async support. The API endpoints were migrated to async but tests remained synchronous, causing "async def functions are not natively supported" errors. This represents the largest category of failures after prompt template fixture errors.

## Outcome

When this ticket is complete:
- All 11 tests in `test_conversion_api_endpoints.py` pass
- All 5 tests in `test_original_markdown.py` pass
- Tests properly use `@pytest.mark.asyncio` decorators
- Async API endpoints are called with `await`
- Mock configurations work correctly with async patterns
- Total passing tests increases from 158 to 174 (16 new passes)

## Scope

### In scope:
- Add `@pytest.mark.asyncio` decorators to all async test functions in:
  - `tests/unit/test_conversion_api_endpoints.py` (11 tests)
  - `tests/unit/test_original_markdown.py` (5 tests)
- Update test method signatures to be `async def`
- Add `await` keywords to API endpoint calls
- Verify mock configurations work with async/await patterns
- Ensure patched async context managers work correctly

### Out of scope:
- Modifying production API endpoint code (no changes to `psychrag_api/` modules)
- Changing test assertions or test logic (only adding async support)
- Creating async database fixtures (standard sync fixtures from T01 are sufficient)
- Fixing other test failures (handled in T03-T05)

## Implementation Plan

### Backend - Test Conversion API Endpoints Module

1. **Read and understand current test structure**:
   - Open `tests/unit/test_conversion_api_endpoints.py`
   - Identify all test methods that call async API functions:
     - `get_file_content()` (async)
     - `update_file_content()` (async)
     - `get_file_suggestion()` (async)
     - `select_file()` (async)
   - Note the current mock patterns used

2. **Update TestGetFileContent class (4 tests)**:
   - Locate: `test_get_style_file_success`, `test_get_file_invalid_type`, `test_get_file_not_found_in_db`, `test_get_file_not_found_on_disk`
   - For each test method:
     ```python
     @pytest.mark.asyncio  # Add this decorator
     async def test_get_style_file_success(  # Change to async def
         self, mock_exists, mock_read_text, mock_load_config, mock_get_session
     ):
         """Test successful retrieval of style.md file."""
         # ... existing mock setup ...

         # Change from:
         # result = get_file_content(io_file_id=1, file_type="style")
         # To:
         result = await get_file_content(io_file_id=1, file_type="style")

         # ... existing assertions ...
     ```
   - Apply same pattern to all 4 tests in this class

3. **Update TestUpdateFileContent class (2 tests)**:
   - Locate: `test_update_file_success`, `test_update_file_invalid_type`
   - Apply same async transformation:
     ```python
     @pytest.mark.asyncio
     async def test_update_file_success(self, ...):
         # ... mocks ...
         await update_file_content(io_file_id=1, request=request_data)
         # ... assertions ...
     ```

4. **Update TestGetFileSuggestion class (2 tests)**:
   - Locate: `test_get_suggestion_hier_wins`, `test_get_suggestion_file_not_found`
   - Apply async transformation:
     ```python
     @pytest.mark.asyncio
     async def test_get_suggestion_hier_wins(self, ...):
         # ... mocks ...
         result = await get_file_suggestion(io_file_id=1)
         # ... assertions ...
     ```

5. **Update TestSelectFile class (3 tests)**:
   - Locate: `test_select_file_success`, `test_select_file_invalid_type`, `test_select_file_target_exists`
   - Apply async transformation:
     ```python
     @pytest.mark.asyncio
     async def test_select_file_success(self, ...):
         # ... mocks ...
         await select_file(io_file_id=1, request=request_data)
         # ... assertions ...
     ```

6. **Verify mock compatibility with async**:
   - Check that `@patch` decorators work with async functions (they do)
   - Verify `mock_get_session` context manager mocking:
     ```python
     # This pattern should work as-is:
     mock_get_session.return_value.__enter__.return_value = mock_session
     ```
   - If any tests use `with` statements on mocked async context managers, update to `async with`

### Backend - Test Original Markdown Module

7. **Update TestOriginalMarkdown class (5 tests)**:
   - Open `tests/unit/test_original_markdown.py`
   - Identify all test methods:
     - `test_get_original_markdown_success`
     - `test_get_original_markdown_not_found_in_db`
     - `test_get_original_markdown_not_found_on_disk`
     - `test_update_original_markdown_success`
     - `test_update_original_markdown_not_found`

8. **Apply async transformation to all 5 tests**:
   ```python
   @pytest.mark.asyncio
   async def test_get_original_markdown_success(self, ...):
       """Test successful retrieval of original markdown."""
       # ... existing mock setup ...

       # Add await to API calls
       result = await get_original_markdown(io_file_id=1)

       # ... existing assertions ...
   ```

9. **Check for async context managers in original_markdown tests**:
   - If the API functions use `async with get_session()`, ensure mocks handle this
   - Typical pattern that should work:
     ```python
     @patch("psychrag_api.routers.original_markdown.get_session")
     async def test_example(self, mock_get_session):
         mock_session = MagicMock()
         mock_get_session.return_value.__aenter__.return_value = mock_session
         # Note: __aenter__ for async context managers, not __enter__
     ```
   - Check if current mocks use `__enter__` (sync) or `__aenter__` (async)
   - Update to `__aenter__` and `__aexit__` if needed

### Verification Steps

10. **Run test_conversion_api_endpoints.py**:
    ```bash
    pytest tests/unit/test_conversion_api_endpoints.py -v
    ```
    - Expected: All 11 tests pass (no "async def functions are not natively supported" errors)
    - If failures: Check mock configurations for async context managers

11. **Run test_original_markdown.py**:
    ```bash
    pytest tests/unit/test_original_markdown.py -v
    ```
    - Expected: All 5 tests pass
    - If failures: Verify `__aenter__`/`__aexit__` for async context manager mocks

12. **Run full test suite to verify no regressions**:
    ```bash
    pytest tests/unit/ -v | grep -E "passed|failed|error"
    ```
    - Expected: 174 passed (158 baseline + 16 new), 35 failed/errors (down from 51)

## Unit Tests

This ticket fixes existing unit tests rather than creating new ones. The testing strategy is:

### Tests to Fix: test_conversion_api_endpoints.py (11 tests)

1. **TestGetFileContent class (4 tests)**:
   - `test_get_style_file_success`: Verify style.md retrieval works
   - `test_get_file_invalid_type`: Verify invalid file type raises error
   - `test_get_file_not_found_in_db`: Verify missing DB record raises 404
   - `test_get_file_not_found_on_disk`: Verify missing file on disk raises 404

2. **TestUpdateFileContent class (2 tests)**:
   - `test_update_file_success`: Verify file content update succeeds
   - `test_update_file_invalid_type`: Verify invalid file type raises error

3. **TestGetFileSuggestion class (2 tests)**:
   - `test_get_suggestion_hier_wins`: Verify hierarchical file takes precedence
   - `test_get_suggestion_file_not_found`: Verify missing file raises 404

4. **TestSelectFile class (3 tests)**:
   - `test_select_file_success`: Verify file selection succeeds
   - `test_select_file_invalid_type`: Verify invalid type raises error
   - `test_select_file_target_exists`: Verify existing target raises error

### Tests to Fix: test_original_markdown.py (5 tests)

5. **TestOriginalMarkdown class (5 tests)**:
   - `test_get_original_markdown_success`: Verify retrieval of original markdown
   - `test_get_original_markdown_not_found_in_db`: Verify DB miss raises 404
   - `test_get_original_markdown_not_found_on_disk`: Verify file miss raises 404
   - `test_update_original_markdown_success`: Verify update succeeds
   - `test_update_original_markdown_not_found`: Verify update of missing file raises error

### Testing Approach

For each test:
- **Add**: `@pytest.mark.asyncio` decorator
- **Change**: `def test_*` → `async def test_*`
- **Add**: `await` before each API function call
- **Verify**: Existing assertions remain unchanged (we're only adding async support)
- **Check**: Mock configurations work with async (update `__enter__` → `__aenter__` if needed)

### Expected Outcomes

- All 16 tests should pass after changes
- Test assertions should remain identical (only execution model changes)
- Mock setup should work with minimal changes (pytest mocks are async-compatible)

## Dependencies and Sequencing

### Must Complete Before:
- **T01**: Test Infrastructure & Database Fixtures
  - Reason: Needs pytest-asyncio installed and configured

### Must Complete Before Starting:
- None (can run in parallel with T03-T05 once T01 is done)

### Blocks If Not Done:
- None (T03-T05 are independent)

### Sequencing Notes:
- Can be implemented immediately after T01 merges
- Independent from T03 (PDF conversion tests) and T04 (prompt template tests)
- Low risk of merge conflicts
- Recommended: Merge before T05 (inspection tests) for cleaner git history

## Clarifications and Assumptions

### Assumptions Made:

1. **Async Context Manager Mocking**: Assuming `get_session()` in API endpoints uses async context managers
   - If so, mocks need `__aenter__`/`__aexit__` instead of `__enter__`/`__exit__`
   - **ACTION REQUIRED**: Check actual API endpoint code to confirm

2. **No Async Database Session Needed**: API endpoints likely use sync sessions within async functions
   - Pattern: `async def endpoint(): with get_session() as session: ...`
   - Standard sync session fixture from T01 is sufficient
   - Alternative: `async def endpoint(): async with get_async_session() as session: ...`
   - **ACTION REQUIRED**: Verify actual session usage pattern in API endpoints

3. **Mock Compatibility**: Assuming unittest.mock works with async functions (it does as of Python 3.8+)
   - `@patch` decorators work on async functions
   - `MagicMock` can mock async context managers with `__aenter__`/`__aexit__`

4. **Test Logic is Correct**: Assuming existing test assertions and mock configurations are correct
   - We're only adding async support, not fixing test logic
   - Any incorrect assertions will be addressed in future tickets if found

5. **No Integration Tests**: These are unit tests with mocks, not integration tests
   - Real database/file operations are mocked
   - Sufficient for this ticket's scope per PRD

### Questions for Product Owner (Non-blocking):

- **Q1**: Should we add integration tests for these endpoints with real database operations?
  - **Current approach**: Unit tests only (per PRD scope)
  - **Recommendation**: Defer integration tests to future ticket if needed

- **Q2**: Are there any async fixtures (e.g., `async_session`) we should use instead of sync fixtures?
  - **Current approach**: Using sync fixtures from T01
  - **Note**: Will update if async session is required

### Blocking Questions (Must Answer Before Implementing):

- **BLOCKER 1**: Do the API endpoints use `async with get_session()` or `with get_session()`?
  - **How to check**: Look at `psychrag_api/routers/conversion.py` and `psychrag_api/routers/original_markdown.py`
  - **Impact**: Determines if we need `__aenter__` or `__enter__` in mocks
  - **ACTION**: Read these files before starting implementation

### Implementer Notes:

> **Before implementing**:
> 1. Read `psychrag_api/routers/conversion.py` to understand actual session usage pattern
> 2. Read `psychrag_api/routers/original_markdown.py` to verify async context manager usage
> 3. Check if any endpoint uses `async with get_session()` or just `with get_session()`
> 4. If unsure about mock patterns, test one file first, verify it passes, then apply to all
>
> **Implementation strategy**:
> 1. Start with `test_conversion_api_endpoints.py` (larger file, 11 tests)
> 2. Fix one test class (e.g., TestGetFileContent), run pytest to verify
> 3. Once pattern is confirmed working, apply to remaining classes
> 4. Then apply same pattern to `test_original_markdown.py` (smaller file, 5 tests)
>
> **If tests still fail after adding async**:
> - Check error message carefully (may need `__aenter__` instead of `__enter__`)
> - Verify pytest-asyncio is actually installed (`pytest --version | grep asyncio`)
> - Check that `asyncio_mode = "auto"` is in pyproject.toml
> - Try running with `-v --tb=short` for better error messages

## Manual Test Plan (Acceptance Criteria)

Run these commands in sequence to verify completion:

```bash
# 1. Run test_conversion_api_endpoints.py in isolation
pytest tests/unit/test_conversion_api_endpoints.py -v
# Expected: 11 passed, 0 failed
# Previously: 11 failed with "async def functions are not natively supported"

# 2. Run test_original_markdown.py in isolation
pytest tests/unit/test_original_markdown.py -v
# Expected: 5 passed, 0 failed
# Previously: 5 failed with "async def functions are not natively supported"

# 3. Verify specific test examples
pytest tests/unit/test_conversion_api_endpoints.py::TestGetFileContent::test_get_style_file_success -v
# Expected: PASSED
pytest tests/unit/test_original_markdown.py::TestOriginalMarkdown::test_get_original_markdown_success -v
# Expected: PASSED

# 4. Run full test suite and check progress
pytest tests/unit/ --tb=no -q | tail -1
# Expected: "174 passed, 35 failed" (down from "158 passed, 51 failed/errors")

# 5. Verify no regressions in baseline passing tests
pytest tests/unit/test_api_endpoints.py tests/unit/test_rag_config_api.py -v
# Expected: All tests still pass (same as baseline)

# 6. Check for "async" errors are gone
pytest tests/unit/ 2>&1 | grep "async def functions are not natively supported"
# Expected: No output (error message should not appear)
```

**Success Criteria**:
- All 6 verification steps pass
- 16 additional tests pass (174 total passing vs 158 baseline)
- No "async def functions are not natively supported" errors
- No regressions in baseline passing tests
- Ready to proceed with T03 (PDF conversion test fixes)
