# T06: Test Documentation & Deferred Issue Creation

## Context

- **PRD**: [PRD.test-suite-fixes.md](PRD.test-suite-fixes.md)
- **PRD Section**: Phase 7: Documentation & Cleanup (Section 5.1, FR7.1-FR7.4)
- This ticket creates documentation for the test patterns established in T01-T05 and creates a GitHub issue to track the single deferred test failure (`test_admin_database_url`). This ensures future contributors can follow established patterns and the deferred work is not forgotten.

## Outcome

When this ticket is complete:
- `tests/README.md` exists documenting test fixture patterns and best practices
- Test patterns are clearly explained with examples (async tests, database fixtures, compare mode)
- GitHub issue created for `test_database.py::test_admin_database_url` fix
- Issue is properly labeled and linked to this PRD
- All T01-T06 work is documented for future maintainers
- Test suite is at 100% passing rate (except the one deferred issue)

## Scope

### In scope:
- Create `tests/README.md` with comprehensive test documentation
- Document database fixture patterns (session, engine)
- Document async test patterns (@pytest.mark.asyncio)
- Document compare mode testing strategy for PDF conversion
- Create GitHub issue for deferred `test_admin_database_url` fix
- Link issue to PRD and T06 ticket
- Add appropriate labels to GitHub issue (bug, testing, deferred)

### Out of scope:
- Fixing the deferred test (that's a future ticket)
- Adding docstrings to every test file (only documenting patterns)
- Creating test style guide beyond what's needed for maintenance
- Setting up pre-commit hooks or CI/CD changes
- Adding pytest plugins beyond what's already in pyproject.toml

## Implementation Plan

### Backend - Create tests/README.md

1. **Create the README structure**:
   - Location: `tests/README.md`
   - Sections:
     - Overview
     - Test Structure
     - Database Fixtures
     - Async Test Patterns
     - PDF Conversion Testing
     - Running Tests
     - Common Issues and Solutions
     - Contributing

2. **Write comprehensive README content**:
   ```markdown
   # Test Suite Documentation

   ## Overview

   This directory contains the unit and integration test suite for psychRAG. The test suite uses pytest with several plugins for async support, database fixtures, and HTML reporting.

   **Current Status**: 202 of 203 tests passing (99.5%)
   - 1 deferred test: `test_database.py::test_admin_database_url` (see [Issue #XXX])

   ## Test Structure

   ```
   tests/
   ├── conftest.py           # Shared fixtures (database, etc.)
   ├── unit/                 # Unit tests
   │   ├── test_*.py        # Test modules
   │   └── results/         # Test run outputs
   └── README.md            # This file
   ```

   ## Database Fixtures

   ### Session Fixture

   All tests requiring database access should use the `session` fixture defined in `conftest.py`:

   ```python
   def test_create_entity(session):
       """Test creating an entity in the database."""
       entity = MyModel(name="test")
       session.add(entity)
       session.commit()

       assert entity.id is not None
   ```

   **Key Points**:
   - Uses in-memory SQLite for speed
   - Function-scoped: each test gets a fresh database
   - Automatic rollback after test completes
   - No manual cleanup needed

   ### Engine Fixture

   For tests that need direct engine access:

   ```python
   def test_with_engine(engine):
       """Test requiring engine access."""
       with engine.connect() as conn:
           result = conn.execute(text("SELECT 1"))
           assert result.scalar() == 1
   ```

   ### Creating Test Data

   Use fixtures for reusable test data:

   ```python
   @pytest.fixture
   def sample_configs(session):
       """Create sample RAG configs for testing."""
       configs = [
           RAGConfig(name="test1", description="Test config 1"),
           RAGConfig(name="test2", description="Test config 2"),
       ]
       for config in configs:
           session.add(config)
       session.commit()
       return configs
   ```

   ## Async Test Patterns

   ### Basic Async Tests

   Use `@pytest.mark.asyncio` for async API endpoint tests:

   ```python
   import pytest

   @pytest.mark.asyncio
   async def test_async_endpoint():
       """Test an async API endpoint."""
       result = await get_file_content(io_file_id=1, file_type="style")
       assert result is not None
   ```

   **Requirements**:
   - `pytest-asyncio` installed (in dev dependencies)
   - `asyncio_mode = "auto"` in `pyproject.toml`
   - Test methods must be `async def`
   - Await all async function calls

   ### Mocking Async Context Managers

   When mocking async endpoints that use `async with`:

   ```python
   @patch("module.get_session")
   @pytest.mark.asyncio
   async def test_with_async_session(mock_get_session):
       mock_session = MagicMock()
       # Note: __aenter__ for async context managers
       mock_get_session.return_value.__aenter__.return_value = mock_session

       result = await endpoint_function()
       assert result is not None
   ```

   ## PDF Conversion Testing

   ### Compare Mode (Default)

   The PDF converter returns tuples by default (compare mode):

   ```python
   def test_pdf_conversion(tmp_path):
       """Test PDF conversion in compare mode."""
       pdf_file = tmp_path / "test.pdf"
       pdf_file.write_text("fake content")

       # Compare mode returns tuple: (style_md, hier_md)
       result = convert_pdf_to_markdown(pdf_file)

       assert isinstance(result, tuple)
       assert len(result) == 2
       style_md, hier_md = result
   ```

   ### File Output Verification

   Compare mode creates multiple output files:

   ```python
   def test_pdf_output_files(tmp_path):
       """Test PDF conversion creates expected files."""
       pdf_file = tmp_path / "test.pdf"
       output_path = tmp_path / "output" / "test.md"

       convert_pdf_to_markdown(pdf_file, output_path=output_path)

       # Verify both files created
       assert (tmp_path / "output" / "test.style.md").exists()
       assert (tmp_path / "output" / "test.hier.md").exists()
       assert (tmp_path / "output" / "test.pdf").exists()  # PDF copied
   ```

   ### Expected Parameters

   When testing `convert_pdf_to_markdown`, include all parameters:

   ```python
   mock_convert.assert_called_once_with(
       pdf_path="test.pdf",
       output_path=str(output_file),
       verbose=False,
       ocr=False,
       hierarchical=True,   # Default
       compare=True,        # Default
       use_gpu=True         # Default
   )
   ```

   ## Running Tests

   ### Run All Tests
   ```bash
   pytest tests/unit/
   ```

   ### Run Specific Test File
   ```bash
   pytest tests/unit/test_rag_config_api.py -v
   ```

   ### Run Specific Test
   ```bash
   pytest tests/unit/test_rag_config_api.py::TestRAGConfigAPI::test_create_config -v
   ```

   ### Run with Coverage
   ```bash
   pytest tests/unit/ --cov=psychrag --cov-report=html
   ```

   ### Run Only Failed Tests
   ```bash
   pytest tests/unit/ --lf
   ```

   ## Common Issues and Solutions

   ### Issue: "fixture 'session' not found"

   **Cause**: Test module cannot find the shared session fixture.

   **Solution**: Ensure `tests/conftest.py` exists and contains the session fixture. Pytest automatically discovers conftest.py files.

   ### Issue: "async def functions are not natively supported"

   **Cause**: Test is async but missing `@pytest.mark.asyncio` decorator.

   **Solution**:
   ```python
   @pytest.mark.asyncio  # Add this
   async def test_async_function():
       result = await some_async_function()
       assert result is not None
   ```

   ### Issue: "AssertionError: assert ('str1', 'str2') == 'str1'"

   **Cause**: Test expects single string but function returns tuple (compare mode).

   **Solution**: Update test to expect tuple:
   ```python
   # Before
   result = convert_pdf_to_markdown(pdf_file)
   assert result == "expected"

   # After
   result = convert_pdf_to_markdown(pdf_file)
   assert isinstance(result, tuple)
   style_md, hier_md = result
   ```

   ### Issue: "table does not exist" in Database Tests

   **Cause**: Model not registered with SQLAlchemy Base.

   **Solution**: Ensure model is imported in `conftest.py`:
   ```python
   # In conftest.py
   from psychrag.data.models import Base
   from psychrag.data.models.your_model import YourModel  # Explicit import
   ```

   ### Issue: Unique Constraint Violations Between Tests

   **Cause**: Database state not properly cleaned between tests.

   **Solution**: Verify conftest.py session fixture includes rollback:
   ```python
   @pytest.fixture(scope="function")
   def session(engine):
       session = SessionLocal()
       yield session
       session.rollback()  # Critical for isolation
       session.close()
   ```

   ## Contributing

   When adding new tests:

   1. **Use Existing Fixtures**: Prefer shared fixtures over creating new ones
   2. **Follow Naming Conventions**: `test_<function_name>_<scenario>`
   3. **Add Docstrings**: Explain what the test verifies
   4. **Test One Thing**: Each test should verify one behavior
   5. **Use Descriptive Assertions**: Clear error messages when tests fail

   ### Example Test Template

   ```python
   def test_function_name_scenario(session):
       """Test that function_name handles scenario correctly.

       This test verifies that when X happens, Y result occurs.
       """
       # Arrange: Set up test data
       entity = MyModel(name="test")
       session.add(entity)
       session.commit()

       # Act: Perform the operation
       result = function_under_test(entity.id)

       # Assert: Verify expected outcome
       assert result.success is True
       assert result.data == "expected_value"
   ```

   ### Test Coverage Goals

   - **Unit Tests**: All public functions and methods
   - **Edge Cases**: Boundary conditions, empty inputs, invalid data
   - **Error Handling**: Expected exceptions and error messages
   - **Integration Points**: Database operations, file I/O, API calls

   ## Related Documentation

   - [PRD: Test Suite Fixes](../documentation/work/PRD.test-suite-fixes.md)
   - [Python Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
   - [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)

   ## Deferred Work

   - **Issue #XXX**: Fix `test_database.py::test_admin_database_url` - Environment variable handling for admin database URL construction
   ```

3. **Verify README formatting**:
   - Check markdown syntax is valid
   - Verify code blocks render correctly
   - Test links work (especially PRD link)

### Backend - Create GitHub Issue

4. **Prepare issue content**:
   - Title: `Fix test_database.py::test_admin_database_url environment variable handling`
   - Body content:

   ```markdown
   ## Description

   The test `test_database.py::TestDatabaseUrl::test_admin_database_url` is currently failing because environment variables set in the test are not being properly read by the `get_admin_database_url()` function.

   **Current Behavior**:
   ```python
   @patch.dict("os.environ", {
       "POSTGRES_ADMIN_USER": "admin",
       "POSTGRES_ADMIN_PASSWORD": "secret",
       "POSTGRES_HOST": "localhost",
       "POSTGRES_PORT": "5432",
   })
   def test_admin_database_url(self):
       url = get_admin_database_url()
       assert "admin:secret" in url  # FAILS: gets "postgres:postgres" instead
   ```

   **Expected Behavior**:
   The function should read environment variables set via `@patch.dict` and return a URL containing the mocked credentials.

   **Actual Behavior**:
   The function returns `postgresql+psycopg://postgres:postgres@127.0.0.1:5432/postgres` instead of using the mocked values.

   ## Root Cause Analysis Needed

   Possible causes:
   1. Environment variables are cached at module import time
   2. `get_admin_database_url()` uses a different method to read config
   3. Mock needs to patch a different location (e.g., config object instead of os.environ)
   4. Function uses pydantic-settings which may cache values

   ## Investigation Steps

   1. Review `psychrag.data.database.get_admin_database_url()` implementation
   2. Determine how it reads configuration (direct os.environ, config object, pydantic settings)
   3. Identify correct patching strategy for tests
   4. Update test to use appropriate mocking approach

   ## Related Work

   - **PRD**: [PRD.test-suite-fixes.md](../documentation/work/PRD.test-suite-fixes.md)
   - **Ticket**: T06 - Test Documentation & Deferred Issue Creation
   - **Deferred in**: Test suite remediation effort (2025-12-04)

   ## Acceptance Criteria

   - [ ] `test_admin_database_url` passes consistently
   - [ ] Mock properly intercepts environment variable reads
   - [ ] Test accurately reflects production behavior
   - [ ] No changes to production code if avoidable (fix test approach first)

   ## Priority

   Low - Test suite is at 99.5% passing (202/203 tests). This is the only remaining failure and does not block development.
   ```

5. **Create the GitHub issue**:
   - Use `gh` CLI tool or GitHub web interface
   - Command: `gh issue create --title "Fix test_database.py::test_admin_database_url environment variable handling" --body "$(cat issue-content.md)" --label bug,testing,deferred`
   - Capture issue number (e.g., #42)

6. **Update tests/README.md with issue number**:
   - Replace `[Issue #XXX]` placeholder with actual issue number
   - Replace `Issue #XXX:` with actual issue number in Deferred Work section

7. **Add issue reference to PRD**:
   - Optional: Update `PRD.test-suite-fixes.md` Open Questions section with issue link
   - Add note: "Question 7 tracked in issue #42"

### Verification Steps

8. **Verify README renders correctly**:
   - View `tests/README.md` in GitHub or a Markdown viewer
   - Check all code blocks render properly
   - Verify all links work

9. **Verify GitHub issue**:
   - Check issue is created with correct labels
   - Verify issue body formatting is correct
   - Confirm issue is in correct repository

10. **Verify test suite status**:
    ```bash
    pytest tests/unit/ --tb=no -q | tail -1
    ```
    - Expected: "202 passed, 1 failed"

11. **Generate test report**:
    ```bash
    pytest tests/unit/ --html=tests/unit/results/final-report.html --self-contained-html
    ```
    - Review HTML report shows clear pass/fail status

## Unit Tests

This ticket is documentation-focused and doesn't require traditional unit tests. Verification is done through:

### Documentation Verification

1. **README Completeness Check**:
   - Does README cover all major test patterns?
   - Are code examples accurate and runnable?
   - Are all sections complete and helpful?

2. **README Accuracy Check**:
   - Test example code snippets by running them
   - Verify fixture usage examples match conftest.py
   - Confirm async patterns match T02 implementation

3. **GitHub Issue Verification**:
   - Issue created with correct information
   - Labels applied (bug, testing, deferred)
   - Issue linked to PRD
   - Issue is discoverable (search for "test_admin_database_url")

### Manual Testing of Examples

Test code snippets from README:

```bash
# 1. Test session fixture example
# Copy example from README to temporary test file and run
pytest tmp_test.py::test_create_entity -v
# Expected: Example runs correctly (or shows what needs fixing)

# 2. Test async pattern example
# Copy async example and verify it matches actual test patterns
grep -A 5 "@pytest.mark.asyncio" tests/unit/test_conversion_api_endpoints.py
# Expected: Matches README example pattern

# 3. Test PDF conversion example
# Verify compare mode example is accurate
grep -A 10 "def test_successful_conversion" tests/unit/test_conv_pdf2md.py
# Expected: Matches README example pattern
```

## Dependencies and Sequencing

### Must Complete Before:
- **T01**: Test Infrastructure (README references conftest.py fixtures)
- **T02**: Async Tests (README documents async patterns)
- **T03**: PDF Tests (README documents compare mode)
- **T04**: Prompt Templates (README references database fixtures)
- **T05**: Cleanup (final test count known)

### Must Complete Before Starting:
- All of T01-T05 must be complete and merged
- Test suite must be at final state (202 passed, 1 failed)

### Blocks If Not Done:
- Nothing - this is the final ticket in the sequence

### Sequencing Notes:
- **MUST BE LAST**: This ticket documents the work done in T01-T05
- Cannot write accurate README until patterns are established
- Cannot create issue until deferred test is confirmed as only remaining failure
- Recommended: Complete after all other tickets are merged

## Clarifications and Assumptions

### Assumptions Made:

1. **All Previous Tickets Complete**: Assuming T01-T05 are done and test suite is at 99.5% passing
   - If not, defer this ticket until they're complete
   - README will be inaccurate if patterns change

2. **GitHub Issue Tracking Used**: Assuming project uses GitHub issues for task tracking
   - If using different system (Jira, etc.), adapt accordingly
   - Issue creation may need different tool/process

3. **Markdown README is Sufficient**: Not creating HTML docs, wiki, or other formats
   - README.md in tests/ directory is standard pytest convention
   - Sufficient for developer onboarding and maintenance

4. **No Style Guide Needed**: Not creating comprehensive Python/pytest style guide
   - Only documenting patterns specific to this test suite
   - Developers expected to know basic pytest

5. **Issue Will Be Fixed Later**: Deferred test is tracked but not prioritized
   - Low priority per PRD (99.5% passing is acceptable)
   - Will be addressed when environment variable handling is refactored

### Questions for Product Owner (Non-blocking):

- **Q1**: Should README include CI/CD test running instructions?
  - **Current approach**: Only local pytest commands
  - **Can add**: GitHub Actions workflow examples if needed

- **Q2**: Should we create additional documentation beyond tests/README.md?
  - **Current approach**: Single README is sufficient
  - **Alternative**: Could add to main project docs/

- **Q3**: What priority should the deferred issue have?
  - **Recommendation**: Low priority (test suite is 99.5% passing)
  - **Label accordingly**: "low-priority" or "nice-to-have"

### No Blocking Questions

All information needed is available from completed work in T01-T05.

### Implementer Notes:

> **Before implementing**:
> 1. **VERIFY ALL PREVIOUS TICKETS COMPLETE**: Check git log, ensure T01-T05 are merged
> 2. Run full test suite to confirm 202 passed, 1 failed
> 3. Review actual implementations in T01-T05 to ensure README examples are accurate
> 4. Check project uses GitHub (not Jira/other) for issue tracking
>
> **Implementation strategy**:
> 1. Start with README structure, fill in sections progressively
> 2. Copy actual working code from test files as examples (don't invent examples)
> 3. Test code snippets as you write them (don't assume they work)
> 4. Write README in multiple passes (structure → content → examples → polish)
> 5. Create GitHub issue last (ensures test suite is at final state)
> 6. Update README with issue number after issue created
>
> **Tips for good documentation**:
> - Use real examples from actual tests (not hypothetical)
> - Show both "before" and "after" for common issues
> - Include command-line examples with expected output
> - Add "why" not just "how" (explain the reasoning)
> - Keep examples minimal but complete (runnable snippets)

## Manual Test Plan (Acceptance Criteria)

Run these commands in sequence to verify completion:

```bash
# 1. Verify tests/README.md exists
ls -la tests/README.md
# Expected: File exists with reasonable size (>5KB)

# 2. Check README content
wc -l tests/README.md
# Expected: At least 200 lines

# 3. Verify README has all sections
grep "^##" tests/README.md
# Expected: Shows all major section headings

# 4. Test README markdown syntax
# (Use markdown linter or viewer)
markdownlint tests/README.md
# Expected: No major syntax errors (or view in IDE/GitHub)

# 5. Verify GitHub issue was created
gh issue list --label testing --search "test_admin_database_url"
# Expected: Issue appears in list

# 6. Check issue has correct labels
gh issue view [ISSUE_NUMBER] --json labels
# Expected: Contains "bug", "testing", "deferred"

# 7. Verify README references issue
grep "Issue #" tests/README.md
# Expected: Shows issue number (not placeholder XXX)

# 8. Verify test suite is at expected state
pytest tests/unit/ --tb=no -q | tail -1
# Expected: "202 passed, 1 failed"

# 9. Verify only deferred test fails
pytest tests/unit/ -v | grep "FAILED"
# Expected: Only "test_database.py::TestDatabaseUrl::test_admin_database_url FAILED"

# 10. Generate final test report
pytest tests/unit/ --html=tests/unit/results/final-report.html --self-contained-html
# Expected: HTML report generated successfully

# 11. Review final report
# Open tests/unit/results/final-report.html in browser
# Expected: Shows 202 passed, 1 failed with clear summary
```

**Success Criteria**:
- All 11 verification steps pass
- `tests/README.md` exists with comprehensive documentation
- GitHub issue created and properly labeled
- README references the GitHub issue
- Test suite status verified at 99.5% passing (202/203)
- Final test report generated
- All T01-T06 work is complete and documented
- Project ready for normal development with maintained test suite
