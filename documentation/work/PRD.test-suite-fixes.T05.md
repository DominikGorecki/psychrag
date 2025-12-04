# T05: Fix Inspection & Remove LLM Parser Tests (9 tests)

## Context

- **PRD**: [PRD.test-suite-fixes.md](PRD.test-suite-fixes.md)
- **PRD Sections**:
  - Phase 5: Inspection Logic Tests (Section 5.1, FR5.1-FR5.4)
  - Phase 6: LLM Citation Parser Tests (Section 5.1, FR6.1-FR6.3)
- This ticket handles two unrelated categories of test issues: (1) 3 inspection tests that expect different file availability logic than what the production module implements, and (2) 6 LLM citation parser tests that reference a refactored-out function (`create_langchain_chat`). These are grouped together as low-priority cleanup items.

## Outcome

When this ticket is complete:
- All 3 tests in `test_inspection.py` pass with updated expectations matching production logic
- All 6 failing tests in `test_llm_citation_parser.py` are removed with explanatory comments
- Test file `test_llm_citation_parser.py` remains but with fewer tests (or is deleted if it becomes empty)
- Total passing tests increases from 199 to 202 (3 new passes, assuming T02+T03+T04 complete)
- Total test count decreases by 6 (removed obsolete tests)
- Final state: 202 passed, 1 failed (only test_database.py::test_admin_database_url remaining, deferred per PRD)

## Scope

### In scope:
- Update `test_inspection.py` tests to match current `get_conversion_inspection()` behavior
- Remove 6 obsolete tests from `test_llm_citation_parser.py`
- Add explanatory comments for removed tests
- Verify inspection logic works as currently implemented (not fixing production code)
- Consider adding TODO comment for future LLM parser test coverage

### Out of scope:
- Modifying production `inspection.py` logic (no changes to `src/psychrag/conversions/inspection.py`)
- Modifying production `llm_citation_parser.py` (no changes to `src/psychrag/utils/llm_citation_parser.py`)
- Re-implementing LLM citation parser tests with new function signatures
- Fixing test_database.py::test_admin_database_url (explicitly deferred per PRD NG5)
- Adding new test coverage beyond fixing existing tests

## Implementation Plan

### Part A: Fix Inspection Logic Tests (3 tests)

#### Backend - Understand Production Inspection Logic

1. **Review get_conversion_inspection() implementation**:
   - The PRD provides the full implementation (lines 1-140 of inspection.py)
   - Key behavior (lines 119-130):
     ```python
     # Check if files exist
     existing_files = []
     for file_name in files_to_check:
         file_path = output_dir / file_name
         if file_path.exists() and file_path.is_file():
             existing_files.append(file_name)

     # Determine availability
     if require_all:
         available = len(existing_files) == len(files_to_check)
     else:
         available = len(existing_files) > 0
     ```
   - All checks use `require_all: True`, so all listed files must exist

2. **Understand test failure patterns**:
   - **test_no_files_present** (line 554): Expects `available=False`, but test shows `available=True`
   - **test_some_files_present** (line 622): Expects `available=False` for titles.md, but gets `True`
   - **test_style_hier_requires_both_files** (line 674): Expects `available=False` when only style.md exists, but gets `True`

3. **Analyze the discrepancy**:
   - Tests mock file existence with `mock_path.exists.return_value`
   - But mocking may not be working correctly for the Path operations
   - The issue is likely in how Path objects are mocked in test setup
   - Production code uses: `(output_dir / file_name).exists()`

#### Backend - Fix test_inspection.py

4. **Fix test_no_files_present** (lines 507-558 in test output):
   - Current issue: Test mocks all files as non-existent but inspection returns available=True
   - Root cause: Mock setup may not properly intercept Path division and exists() calls
   - Solution: Review mock setup, ensure Path operations are properly patched

   ```python
   @patch("psychrag.conversions.inspection.get_session")
   @patch("psychrag.conversions.inspection.load_config")
   def test_no_files_present(self, mock_load_config, mock_get_session):
       """Test inspection when no files are present."""
       # ... existing mock setup ...

       # The key fix: Ensure Path mocking properly intercepts operations
       with patch("psychrag.conversions.inspection.Path") as mock_path_class:
           def mock_path_constructor(path_str):
               mock_path = MagicMock(spec=Path)
               mock_path.exists.return_value = False  # No files exist
               mock_path.is_file.return_value = False
               mock_path.__truediv__ = lambda self, other: mock_path_constructor(str(other))
               return mock_path

           mock_path_class.return_value = mock_path_constructor("/output")
           mock_path_class.side_effect = mock_path_constructor

           result = get_conversion_inspection(1)

       # Verify results - ALL should be unavailable
       assert len(result) == 5
       assert all(not item.available for item in result)
   ```

5. **Fix test_some_files_present** (lines 559-626 in test output):
   - Current issue: Test expects titles.md check to fail but it passes
   - The test mocks style.md, hier.md, and toc_titles.md as existing
   - titles.md should NOT exist, so `available` should be False
   - Review the mock setup for correct file list

   ```python
   @patch("psychrag.conversions.inspection.get_session")
   @patch("psychrag.conversions.inspection.load_config")
   def test_some_files_present(self, mock_load_config, mock_get_session):
       """Test inspection when only some files are present."""
       # ... existing mock setup ...

       # Mock file existence - only style.md, hier.md, and toc_titles.md exist
       existing_files = {
           "test.style.md",
           "test.hier.md",
           "test.toc_titles.md"
       }

       with patch("psychrag.conversions.inspection.Path") as mock_path_class:
           def mock_path_constructor(path_str):
               mock_path = MagicMock(spec=Path)
               # Properly extract filename and check existence
               path_obj = Path(path_str)
               filename = path_obj.name if path_obj.is_absolute() else path_str

               mock_path.exists.return_value = filename in existing_files
               mock_path.is_file.return_value = filename in existing_files
               mock_path.name = filename
               mock_path.__truediv__ = lambda self, other: mock_path_constructor(str(other))
               return mock_path

           mock_path_class.return_value = mock_path_constructor("/output")
           mock_path_class.side_effect = mock_path_constructor

           result = get_conversion_inspection(1)

       # Verify results
       assert len(result) == 5

       # inspect_style_hier: requires BOTH style.md and hier.md (both exist)
       assert result[0].name == "inspect_style_hier"
       assert result[0].available is True

       # inspect_toc_titles: requires toc_titles.md (exists)
       assert result[1].name == "inspect_toc_titles"
       assert result[1].available is True

       # inspect_titles: requires titles.md (does NOT exist)
       assert result[2].name == "inspect_titles"
       assert result[2].available is False  # KEY FIX: Expect False
   ```

6. **Fix test_style_hier_requires_both_files** (lines 627-678 in test output):
   - Current issue: Test expects available=False when only style.md exists, gets True
   - The test should verify that BOTH files are required
   - Fix mock setup to ensure hier.md is properly detected as missing

   ```python
   @patch("psychrag.conversions.inspection.get_session")
   @patch("psychrag.conversions.inspection.load_config")
   def test_style_hier_requires_both_files(self, mock_load_config, mock_get_session):
       """Test that style_hier inspection requires both style.md and hier.md."""
       # ... existing mock setup ...

       # Mock file existence - only style.md exists, NOT hier.md
       existing_files = {"test.style.md"}

       with patch("psychrag.conversions.inspection.Path") as mock_path_class:
           def mock_path_constructor(path_str):
               mock_path = MagicMock(spec=Path)
               path_obj = Path(path_str)
               filename = path_obj.name

               # Check if this specific file exists
               mock_path.exists.return_value = filename in existing_files
               mock_path.is_file.return_value = filename in existing_files
               mock_path.name = filename
               mock_path.__truediv__ = lambda self, other: mock_path_constructor(str(other))
               return mock_path

           mock_path_class.return_value = mock_path_constructor("/output")
           mock_path_class.side_effect = mock_path_constructor

           result = get_conversion_inspection(1)

       # Verify that style_hier is NOT available (requires both files)
       style_hier_item = next(item for item in result if item.name == "inspect_style_hier")
       assert style_hier_item.available is False  # Only style.md exists, hier.md missing
   ```

7. **Alternative approach - simplify mocking**:
   - If complex Path mocking continues to fail, consider simpler approach:
   - Patch at the file existence check level rather than Path class level
   - Use `patch("pathlib.Path.exists")` with side_effect function:

   ```python
   def exists_side_effect(self):
       # self is the Path object being checked
       return self.name in existing_files

   with patch.object(Path, "exists", side_effect=exists_side_effect):
       with patch.object(Path, "is_file", side_effect=exists_side_effect):
           result = get_conversion_inspection(1)
   ```

### Part B: Remove LLM Citation Parser Tests (6 tests)

8. **Review test_llm_citation_parser.py structure**:
   - Open `tests/unit/test_llm_citation_parser.py`
   - Identify the 6 failing tests (all fail with: "does not have the attribute 'create_langchain_chat'")
   - Count total tests in file to determine if any should remain

9. **Remove obsolete tests**:
   - If file contains ONLY these 6 tests, consider two options:
     - **Option A**: Delete entire file and add note to commit message
     - **Option B**: Keep empty file with explanatory module docstring

   - If file contains other passing tests, keep the file and remove only the 6 failing tests

10. **Add explanatory comments**:
    - At top of file (or in place of removed tests), add:

    ```python
    """
    Unit tests for LLM citation parser.

    NOTE: Several tests were removed as of 2025-12-04 because the create_langchain_chat
    function was refactored out during module restructuring. The citation parsing
    functionality may still exist but with a different API.

    Removed tests:
    - test_parse_apa_citation_success
    - test_parse_mla_citation_success
    - test_parse_handles_partial_data
    - test_parse_llm_error_wrapped
    - test_parse_chicago_citation
    - test_parse_journal_article_with_doi

    TODO: If citation parsing functionality still exists, add new tests for the current API.
    Review psychrag.utils.llm_citation_parser module to determine current public interface.
    """
    ```

11. **Check for remaining tests**:
    - If any tests remain in the file, verify they pass
    - If all tests are removed and file is kept empty, ensure it doesn't break test discovery

12. **Consider checking production module**:
    - Optionally read `src/psychrag/utils/llm_citation_parser.py` to see current state
    - Document in TODO if there's a replacement function that should be tested
    - Don't implement new tests (out of scope), just note for future work

### Verification Steps

13. **Run test_inspection.py**:
    ```bash
    pytest tests/unit/test_inspection.py -v
    ```
    - Expected: All tests pass (3 tests)
    - Previously: 3 failed

14. **Verify specific inspection tests**:
    ```bash
    pytest tests/unit/test_inspection.py::TestGetConversionInspection::test_no_files_present -v
    pytest tests/unit/test_inspection.py::TestGetConversionInspection::test_some_files_present -v
    pytest tests/unit/test_inspection.py::TestGetConversionInspection::test_style_hier_requires_both_files -v
    ```
    - Expected: All PASSED

15. **Check test_llm_citation_parser.py**:
    ```bash
    pytest tests/unit/test_llm_citation_parser.py -v
    ```
    - Expected: Either "no tests ran" (if file deleted/emptied) or remaining tests pass
    - Should NOT see: "AttributeError: ... does not have the attribute 'create_langchain_chat'"

16. **Run full test suite**:
    ```bash
    pytest tests/unit/ --tb=no -q | tail -1
    ```
    - Expected: "202 passed, 1 failed" (assuming T02+T03+T04 complete)
    - The 1 remaining failure is test_database.py::test_admin_database_url (deferred)

## Unit Tests

This ticket handles two types of test changes:

### Part A: Tests to Fix (test_inspection.py - 3 tests)

1. **test_no_files_present**:
   - **Current failure**: `assert False` (some items show available=True when should be False)
   - **Root cause**: Mock not properly intercepting Path operations
   - **Fix**: Improve mock setup to properly simulate non-existent files

2. **test_some_files_present**:
   - **Current failure**: `AssertionError: assert True is False` for titles.md check
   - **Root cause**: Mock indicates file exists when it shouldn't
   - **Fix**: Ensure only specific files (style, hier, toc_titles) are mocked as existing

3. **test_style_hier_requires_both_files**:
   - **Current failure**: `AssertionError: assert True is False` for style_hier availability
   - **Root cause**: Mock shows both files exist when only style.md should exist
   - **Fix**: Mock only style.md as existing, verify hier.md is detected as missing

### Part B: Tests to Remove (test_llm_citation_parser.py - 6 tests)

4. **TestParseCitationWithLLM class (5 tests to remove)**:
   - test_parse_apa_citation_success
   - test_parse_mla_citation_success
   - test_parse_handles_partial_data
   - test_parse_llm_error_wrapped
   - test_parse_chicago_citation

5. **TestIntegrationScenarios class (1 test to remove)**:
   - test_parse_journal_article_with_doi

**Removal strategy**:
- Delete test methods entirely
- Add explanatory docstring to module or class
- Add TODO for future test coverage if functionality still exists

### No New Tests Created

Per PRD scope, we are only fixing/removing existing tests, not adding new coverage.

## Dependencies and Sequencing

### Must Complete Before:
- **T01**: Test Infrastructure & Database Fixtures (for pytest setup)

### Must Complete Before Starting:
- None (can run in parallel with T02, T03, T04 after T01)

### Blocks If Not Done:
- None (this is the last test fix ticket before documentation)

### Sequencing Notes:
- Can be implemented immediately after T01 merges
- Independent from T02 (async), T03 (PDF), T04 (prompt templates)
- Lowest priority of all test fix tickets
- Recommended: Implement last, after T02-T04 are complete
- Clean up before T06 (documentation)

## Clarifications and Assumptions

### Assumptions Made:

1. **Inspection Logic is Correct**: Production `get_conversion_inspection()` logic is correct as-is
   - Not fixing production code per PRD constraint
   - Tests should match production behavior
   - Any bugs in production logic are out of scope

2. **Path Mocking Needs Improvement**: Current mock setup doesn't properly simulate Path operations
   - The mock needs to handle `Path / str` operations (`__truediv__`)
   - The mock needs to handle `.exists()` and `.is_file()` correctly
   - May need to use `side_effect` for dynamic behavior

3. **LLM Parser Function is Gone**: `create_langchain_chat` was refactored out completely
   - No replacement function to test (or it has different signature)
   - Removing tests is appropriate per PRD direction
   - Not investigating what replaced it (out of scope)

4. **Test Database Not Needed**: Inspection tests mock database and filesystem, don't need real DB
   - Tests use `@patch` for database session
   - Tests use `@patch` for config and filesystem
   - No dependency on T01's session fixture

5. **Only One Test Should Remain Failing**: After this ticket, only test_admin_database_url should fail
   - This is the deferred test per PRD NG5
   - All other tests should pass
   - Target: 202 passed, 1 failed (out of 203 total after removing 6)

### Questions for Product Owner (Non-blocking):

- **Q1**: Should we investigate what replaced `create_langchain_chat` and add new tests?
  - **Current approach**: No, out of scope per PRD
  - **Recommendation**: Add TODO comment, defer to future ticket

- **Q2**: Is the inspection logic behavior correct (marking files available when they don't exist in some cases)?
  - **Current approach**: Assume production is correct, update tests to match
  - **Note**: If production has bugs, that's a separate issue

### Blocking Questions:

None - all information needed for implementation is available.

### Implementer Notes:

> **Before implementing**:
> 1. Read current `test_inspection.py` to understand existing mock patterns
> 2. Test one fix at a time - start with `test_no_files_present`
> 3. If Path mocking is too complex, try simpler `patch.object(Path, "exists")` approach
> 4. For LLM parser tests, check if file has any other tests before deleting
>
> **Implementation strategy**:
> 1. Start with Part B (LLM parser removal) - it's simpler
> 2. Remove the 6 tests, add explanatory comments
> 3. Run pytest to verify they're gone
> 4. Then tackle Part A (inspection tests)
> 5. Fix one test at a time, verify each passes before moving to next
> 6. If stuck on Path mocking, consider asking for help or trying alternative approach
>
> **If inspection tests still fail after mock updates**:
> - Add debug prints in test to see what's being checked: `print(f"Checking {file_name}: {exists}")`
> - Run single test with `-s` flag to see output: `pytest test_file.py::test_name -s`
> - Verify the mock is actually being called: add `assert mock.called` after test
> - Consider patching at a different level (e.g., `pathlib.Path` vs `inspection.Path`)

## Manual Test Plan (Acceptance Criteria)

Run these commands in sequence to verify completion:

```bash
# Part B: Verify LLM parser tests are removed

# 1. Check LLM parser tests status
pytest tests/unit/test_llm_citation_parser.py -v 2>&1 | grep "create_langchain_chat"
# Expected: No output (error should be gone)

# 2. Run LLM parser test file
pytest tests/unit/test_llm_citation_parser.py -v
# Expected: Either "no tests ran" or remaining tests pass (none should fail)

# Part A: Verify inspection tests are fixed

# 3. Run test_inspection.py
pytest tests/unit/test_inspection.py -v
# Expected: All tests PASSED (was 3 failed)

# 4. Run specific inspection tests
pytest tests/unit/test_inspection.py::TestGetConversionInspection::test_no_files_present -v
# Expected: PASSED (was: assert False)

pytest tests/unit/test_inspection.py::TestGetConversionInspection::test_some_files_present -v
# Expected: PASSED (was: assert True is False)

pytest tests/unit/test_inspection.py::TestGetConversionInspection::test_style_hier_requires_both_files -v
# Expected: PASSED (was: assert True is False)

# Overall verification

# 5. Run full test suite and check final state
pytest tests/unit/ --tb=no -q
# Expected: "202 passed, 1 failed"
# The 1 failed should be test_database.py::test_admin_database_url (deferred)

# 6. Verify only the deferred test fails
pytest tests/unit/test_database.py::TestDatabaseUrl::test_admin_database_url -v
# Expected: FAILED (this is the expected/deferred failure)

# 7. Verify no other failures
pytest tests/unit/ -v | grep "FAILED" | grep -v "test_admin_database_url"
# Expected: No output (only test_admin_database_url should fail)

# 8. Count total tests
pytest tests/unit/ --collect-only -q | tail -1
# Expected: "203 tests collected" (down from 209: removed 6 LLM parser tests)

# 9. Verify test file syntax
python -m py_compile tests/unit/test_inspection.py
python -m py_compile tests/unit/test_llm_citation_parser.py
# Expected: No syntax errors
```

**Success Criteria**:
- All 9 verification steps pass
- 202 tests passing (up from 199)
- Only 1 test failing (test_admin_database_url, which is deferred)
- 6 tests removed (203 total tests vs 209 original)
- No "create_langchain_chat" errors
- No inspection test assertion failures
- Ready to proceed with T06 (documentation)
