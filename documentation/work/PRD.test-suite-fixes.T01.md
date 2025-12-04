COMPLETE

# T01: Test Infrastructure & Database Fixtures

## Context

- **PRD**: [PRD.test-suite-fixes.md](PRD.test-suite-fixes.md)
- **PRD Section**: Phase 1: Infrastructure & Dependencies (Section 5.1, FR1.1-FR1.3)
- This ticket establishes the foundational test infrastructure needed by all subsequent test fixes. Without shared database fixtures and async support, 35+ tests cannot be fixed. This unblocks the entire test suite remediation effort.

## Outcome

When this ticket is complete:
- `pytest-asyncio` is installed and configured in the project
- A `tests/conftest.py` file exists with shared database fixtures (`engine`, `session`)
- All test modules can import and use the `session` fixture
- Running `pytest --fixtures` shows the new fixtures are available
- No tests are broken by the infrastructure additions (baseline: 158 passing tests maintained)

## Scope

### In scope:
- Add `pytest-asyncio` to `[project.optional-dependencies].dev` in `pyproject.toml`
- Configure pytest-asyncio mode in `[tool.pytest.ini_options]`
- Create `tests/conftest.py` with database fixtures
- Implement `engine` fixture (function-scoped, in-memory SQLite)
- Implement `session` fixture (function-scoped, with automatic rollback)
- Verify fixtures work by running existing passing tests

### Out of scope:
- Fixing any failing tests (handled in T02-T05)
- Creating the `sample_templates` fixture (specific to prompt template tests, handled in T04)
- Async fixtures or async database session handling (handled in T02)
- Documentation of test patterns (handled in T06)

## Implementation Plan

### Backend - Dependencies

1. **Update pyproject.toml**:
   - Open `pyproject.toml`
   - Locate `[project.optional-dependencies]` section, subsection `dev = [...]`
   - Add `"pytest-asyncio",` to the dev dependencies list
   - Maintain alphabetical order if the list is sorted

2. **Configure pytest-asyncio**:
   - In `pyproject.toml`, locate `[tool.pytest.ini_options]` section
   - Add configuration line: `asyncio_mode = "auto"`
   - This enables automatic detection of async tests without requiring explicit event loop fixtures

3. **Install dependencies**:
   - Run `pip install -e ".[dev]"` to install the new dependency
   - Verify installation: `pytest --version` should show pytest-asyncio plugin loaded

### Backend - Test Fixtures

4. **Create tests/conftest.py**:
   ```python
   """Shared test fixtures for the test suite.

   This module provides database fixtures and other shared test utilities.
   """

   import pytest
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker, Session
   from psychrag.data.models import Base


   @pytest.fixture(scope="function")
   def engine():
       """Create in-memory SQLite engine for tests.

       Each test gets a fresh database. The engine is torn down after
       the test completes.

       Yields:
           SQLAlchemy Engine instance with all tables created.
       """
       # Create in-memory SQLite database
       engine = create_engine("sqlite:///:memory:")

       # Create all tables defined in models
       Base.metadata.create_all(engine)

       yield engine

       # Cleanup: drop all tables
       Base.metadata.drop_all(engine)
       engine.dispose()


   @pytest.fixture(scope="function")
   def session(engine) -> Session:
       """Create database session for tests with automatic rollback.

       Each test gets a fresh session connected to the test database.
       After the test completes, all changes are rolled back to ensure
       test isolation.

       Args:
           engine: The test database engine fixture.

       Yields:
           SQLAlchemy Session instance.
       """
       # Create a session factory bound to the test engine
       TestingSessionLocal = sessionmaker(bind=engine)

       # Create a new session for this test
       session = TestingSessionLocal()

       yield session

       # Cleanup: rollback any changes and close the session
       session.rollback()
       session.close()
   ```

5. **Verify Base model import**:
   - Check that `psychrag.data.models` exports a `Base` object
   - If not, locate the actual base declarative class (e.g., `psychrag.data.models.base`)
   - Update the import in conftest.py accordingly
   - Common patterns to check:
     - `from psychrag.data.models import Base`
     - `from psychrag.data.models.base import Base`
     - `from psychrag.data.database import Base`

6. **Verify fixture availability**:
   ```bash
   pytest --fixtures tests/
   ```
   - Should show `engine` and `session` fixtures in the output
   - Should show description text from docstrings

### Verification Steps

7. **Run existing passing tests**:
   ```bash
   pytest tests/unit/test_api_endpoints.py -v
   pytest tests/unit/test_rag_config_api.py -v
   ```
   - These tests should still pass (baseline: 15 + 14 = 29 tests)
   - If any break, investigate fixture conflicts

8. **Test fixture isolation**:
   - Create a temporary test file `tests/test_fixtures.py`:
     ```python
     def test_session_fixture_available(session):
         """Verify session fixture is available."""
         assert session is not None

     def test_engine_fixture_available(engine):
         """Verify engine fixture is available."""
         assert engine is not None
     ```
   - Run: `pytest tests/test_fixtures.py -v`
   - Should show 2 passing tests
   - Delete the temporary test file after verification

9. **Verify pytest-asyncio**:
   - Check pytest output for: `plugins: anyio-4.11.0, pytest-asyncio-X.X.X, ...`
   - Create temporary async test:
     ```python
     import pytest

     @pytest.mark.asyncio
     async def test_async_support():
         assert True
     ```
   - Should pass without "async def functions are not natively supported" error
   - Delete after verification

## Unit Tests

Since this ticket creates test infrastructure rather than production code, the testing strategy is verification-based:

### Verification Tests (Run Manually)

1. **Test: Fixture availability**
   - Command: `pytest --fixtures tests/ | grep -A 5 "session\|engine"`
   - Expected: Both fixtures appear with their docstrings

2. **Test: Baseline tests still pass**
   - Command: `pytest tests/unit/test_api_endpoints.py tests/unit/test_rag_config_api.py -v`
   - Expected: All previously passing tests (29+) still pass

3. **Test: Session fixture isolation**
   - Create two tests that modify the same model
   - Verify changes in test 1 don't affect test 2
   - Example:
     ```python
     from psychrag.data.models.rag_config import RAGConfig

     def test_session_isolation_1(session):
         config = RAGConfig(name="test", description="test")
         session.add(config)
         session.commit()
         assert session.query(RAGConfig).count() == 1

     def test_session_isolation_2(session):
         # Should start with empty database
         assert session.query(RAGConfig).count() == 0
     ```

4. **Test: Pytest-asyncio installation**
   - Command: `pytest --version`
   - Expected output includes: `plugins: ... pytest-asyncio-X.X.X ...`

### No Traditional Unit Tests Required

This ticket does not require traditional unit test files because:
- We're creating test infrastructure, not production code
- Verification is done by running the test suite itself
- Subsequent tickets (T02-T05) will exercise these fixtures extensively

## Dependencies and Sequencing

### Must Complete Before:
- None (this is the first ticket)

### Must Complete Before Starting:
- **T02**: Async tests need pytest-asyncio configuration
- **T04**: Prompt template tests need the `session` fixture

### Blocks If Not Done:
- All subsequent tickets depend on this infrastructure
- Without this, 35+ test failures cannot be fixed

### Sequencing Notes:
- This ticket should be merged first
- Can be implemented and tested independently
- Low risk of conflicts with other work

## Clarifications and Assumptions

### Assumptions Made:

1. **SQLite Compatibility**: Assuming SQLAlchemy models are compatible with SQLite for testing
   - Risk: Some Postgres-specific features (JSON operators, arrays) might not work
   - Mitigation: If issues arise, can switch to test Postgres container in future ticket

2. **Function-Scoped Fixtures**: Using `scope="function"` for maximum test isolation
   - Trade-off: Slower test execution vs guaranteed isolation
   - Alternative: Could use `scope="module"` for speed if tests are proven independent

3. **Base Model Location**: Assuming `psychrag.data.models` exports `Base`
   - **ACTION REQUIRED**: Verify actual import path before implementing

4. **No Async Session Needed Yet**: Standard sync session is sufficient for T04 (prompt template tests)
   - Async session support will be added in T02 if needed for API endpoint tests

5. **Pytest-asyncio Mode**: Using `asyncio_mode = "auto"` for convenience
   - Alternative: `asyncio_mode = "strict"` requires explicit `@pytest.mark.asyncio`
   - Auto mode is chosen for compatibility with existing test patterns

### Questions for Product Owner (Non-blocking):

- **Q1**: Should we use SQLite for all tests, or eventually migrate to test Postgres containers for higher fidelity?
  - **Recommendation**: Start with SQLite (faster, simpler), revisit if dialect issues arise

- **Q2**: Should fixtures be function-scoped (slow but safe) or module-scoped (fast but risky)?
  - **Current approach**: Function-scoped per PRD recommendation
  - **Can optimize later** if test suite becomes too slow

### Implementer Notes:

> **Before implementing**:
> 1. Verify the correct import path for `Base` by checking `src/psychrag/data/models/__init__.py` or `src/psychrag/data/database.py`
> 2. Run the baseline test suite and note the exact pass count (should be 158 passed)
> 3. After implementing, verify the baseline count is maintained
>
> **If SQLite compatibility issues arise**:
> - Document the specific model/feature that's incompatible
> - Consider adding a postgres test container (testcontainers-python)
> - Flag for discussion before proceeding with alternative approach

## Manual Test Plan (Acceptance Criteria)

Run these commands in sequence to verify completion:

```bash
# 1. Verify pytest-asyncio is installed
pytest --version | grep pytest-asyncio
# Expected: pytest-asyncio-X.X.X appears in plugins list

# 2. Verify fixtures are available
pytest --fixtures tests/ | grep -E "session|engine"
# Expected: Both fixtures appear with docstrings

# 3. Verify baseline tests still pass
pytest tests/unit/test_api_endpoints.py tests/unit/test_rag_config_api.py -v
# Expected: Same number of passing tests as before (29+)

# 4. Run full test suite to verify no regressions
pytest tests/unit/ -v --tb=short
# Expected: 158 passed (same as baseline), same 51 failures/errors

# 5. Verify conftest.py exists and is valid Python
python -m py_compile tests/conftest.py
# Expected: No syntax errors

# 6. Quick fixture smoke test
pytest -c /dev/null --collect-only tests/unit/test_prompt_template_model.py 2>&1 | grep "fixture 'session' not found"
# Expected: Error should NOT appear (fixture is now available)
```

**Success Criteria**:
- All 6 verification steps pass
- No reduction in baseline passing test count (158 tests)
- `tests/conftest.py` exists with proper fixtures
- `pyproject.toml` includes pytest-asyncio in dev dependencies
- Ready to begin T02 (async test fixes)
