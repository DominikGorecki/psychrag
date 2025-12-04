# T04: Fix Prompt Template Model Tests (19 tests)

## Context

- **PRD**: [PRD.test-suite-fixes.md](PRD.test-suite-fixes.md)
- **PRD Section**: Phase 4: Prompt Template Tests (Section 5.1, FR4.1-FR4.5)
- This ticket fixes 19 ERROR conditions (not failures) in `test_prompt_template_model.py` caused by missing `session` fixture. All tests in this file request a `session` parameter but pytest cannot find the fixture, causing setup errors before tests even run. This is the largest single category of test issues and blocks testing of the entire PromptTemplate model.

## Outcome

When this ticket is complete:
- All 19 tests in `test_prompt_template_model.py` can run (no more "fixture 'session' not found" errors)
- The shared `session` fixture from `tests/conftest.py` (created in T01) is properly utilized
- The `sample_templates` fixture is updated to depend on `session` fixture
- All 19 tests pass with proper database isolation
- Total passing tests increases from 180 to 199 (19 new passes, assuming T02+T03 complete)

## Scope

### In scope:
- Update `test_prompt_template_model.py` to use shared `session` fixture from `tests/conftest.py`
- Update or create `sample_templates` fixture to properly depend on `session`
- Ensure test isolation (each test gets clean database state)
- Verify all 19 tests pass with in-memory SQLite database
- Handle any SQLite vs Postgres compatibility issues if they arise

### Out of scope:
- Modifying production PromptTemplate model code (no changes to `src/psychrag/data/models/`)
- Adding new test cases or test coverage
- Performance optimization of test database setup
- Migration to test Postgres containers (defer to future ticket if needed)
- Fixing test_database.py::test_admin_database_url (deferred per PRD)

## Implementation Plan

### Backend - Understand Current Test Structure

1. **Review test_prompt_template_model.py structure**:
   - Open `tests/unit/test_prompt_template_model.py`
   - Identify all test classes and their test methods:
     - `TestPromptTemplateCreation` (3 tests)
     - `TestPromptTemplateValidation` (3 tests)
     - `TestPromptTemplateConstraints` (4 tests)
     - `TestPromptTemplateQueries` (5 tests)
     - `TestPromptTemplateLangChainCompatibility` (2 tests)
     - `TestPromptTemplateUpdates` (2 tests)
   - Total: 19 test methods

2. **Check for existing fixture definitions**:
   - Look for `@pytest.fixture` definitions in the file
   - Specifically find `sample_templates` fixture (mentioned in error output line 112)
   - Note its current dependencies and implementation

3. **Verify PromptTemplate model import**:
   - Confirm import path: likely `from psychrag.data.models.prompt_template import PromptTemplate`
   - Or: `from psychrag.data.models import PromptTemplate`
   - Verify model is properly mapped to SQLAlchemy Base

### Backend - Update Fixtures

4. **Locate or create sample_templates fixture**:
   - If fixture exists in `test_prompt_template_model.py`:
     ```python
     @pytest.fixture
     def sample_templates(session):  # Add session dependency
         """Create sample prompt templates for testing."""
         templates = [
             PromptTemplate(
                 function_tag="test_function",
                 version=1,
                 template_content="Test template {variable}",
                 is_active=True,
                 description="Test template"
             ),
             PromptTemplate(
                 function_tag="test_function",
                 version=2,
                 template_content="Test template v2 {variable}",
                 is_active=False,
                 description="Test template version 2"
             ),
             PromptTemplate(
                 function_tag="other_function",
                 version=1,
                 template_content="Other template",
                 is_active=True,
                 description="Other function template"
             ),
         ]

         for template in templates:
             session.add(template)
         session.commit()

         return templates
     ```

   - If fixture doesn't exist, create it following the pattern above
   - Adjust template data based on actual test requirements (read test methods to understand needs)

5. **Verify session fixture is available**:
   - The `session` fixture is defined in `tests/conftest.py` (from T01)
   - No changes needed to individual test methods - they already request `session` parameter
   - pytest will automatically inject the fixture from conftest.py

### Backend - Handle Model-Specific Requirements

6. **Check PromptTemplate model fields**:
   - Review `src/psychrag/data/models/prompt_template.py` (or wherever model is defined)
   - Identify required fields:
     - `function_tag` (required, per error line 86)
     - `template_content` (required, per error line 94)
     - `version` (required, with validation)
     - `is_active` (boolean, defaults handled)
     - `created_at`, `updated_at` (timestamps, auto-generated)
   - Ensure fixture provides all required fields

7. **Handle unique constraints**:
   - Model likely has unique constraint on `(function_tag, version)` per line 119
   - Ensure `sample_templates` fixture uses unique combinations
   - Example: `("test_function", 1)`, `("test_function", 2)`, `("other_function", 1)`

8. **Check for validation constraints**:
   - Version must be positive (lines 78, 91, 103)
   - Ensure fixture uses `version >= 1`
   - Handle check constraint: `version > 0`

### Backend - Update Test Methods (if needed)

9. **Review test methods for fixture usage**:
   - Most tests already request `session` parameter - no changes needed
   - Some tests request `sample_templates` - verify this fixture now works
   - Example test signature: `def test_query_by_function_tag(self, session, sample_templates):`

10. **Check for test-specific fixture needs**:
    - Tests may create their own template instances within test methods
    - Verify they use the injected `session` properly
    - Example pattern:
      ```python
      def test_create_prompt_template(self, session):
          template = PromptTemplate(
              function_tag="test",
              version=1,
              template_content="content"
          )
          session.add(template)
          session.commit()
          assert template.id is not None
      ```

### Backend - Handle SQLite Compatibility

11. **Test for SQLite compatibility issues**:
    - Run tests to identify any Postgres-specific features that fail on SQLite
    - Common issues:
      - JSON operators (use `.astext` instead of `->`)
      - Array types (may need workarounds)
      - Specific date/time functions
    - If issues found, document them (don't fix production code per constraint)

12. **Handle datetime fields**:
    - PromptTemplate likely has `created_at` and `updated_at` fields
    - Ensure these work with SQLite (usually fine with SQLAlchemy defaults)
    - Check for UTC vs local time issues if tests fail

### Verification Steps

13. **Run test_prompt_template_model.py**:
    ```bash
    pytest tests/unit/test_prompt_template_model.py -v
    ```
    - Expected: 19 tests run (no setup errors)
    - Expected: All 19 pass (or at least run and show clear failures, not fixture errors)
    - Previous: 19 errors with "fixture 'session' not found"

14. **Verify fixture injection**:
    ```bash
    pytest tests/unit/test_prompt_template_model.py::TestPromptTemplateCreation::test_create_prompt_template -v
    ```
    - Expected: Test runs (no fixture error)
    - Expected: PASSED

15. **Check sample_templates fixture**:
    ```bash
    pytest tests/unit/test_prompt_template_model.py::TestPromptTemplateQueries::test_query_by_function_tag -v
    ```
    - Expected: Test uses sample_templates fixture successfully
    - Expected: PASSED

16. **Verify test isolation**:
    ```bash
    pytest tests/unit/test_prompt_template_model.py::TestPromptTemplateConstraints::test_unique_constraint -v --count=3
    ```
    - Run same test 3 times (if pytest-repeat installed, otherwise run manually 3x)
    - Expected: All runs pass (no "unique constraint violation" from previous test data)

### Backend - Troubleshooting Common Issues

17. **If tests still fail with database errors**:
    - Check if Base.metadata includes PromptTemplate table
    - Verify model imports in `psychrag.data.models.__init__.py`
    - May need to explicitly import model for table creation:
      ```python
      # In tests/conftest.py
      from psychrag.data.models.prompt_template import PromptTemplate  # Ensure model is registered
      ```

18. **If unique constraint tests fail**:
    - Verify `sample_templates` uses different (function_tag, version) combinations
    - Check that session.rollback() in conftest.py is working properly
    - Try adding explicit session.expunge_all() if needed

## Unit Tests

This ticket fixes 19 existing unit tests rather than creating new ones:

### Tests to Fix (All in test_prompt_template_model.py)

#### TestPromptTemplateCreation (3 tests)
1. **test_create_prompt_template**:
   - **Current error**: `fixture 'session' not found`
   - **Fix**: Session fixture now available from conftest.py
   - **Tests**: Creating a PromptTemplate and committing to database

2. **test_default_values**:
   - **Current error**: `fixture 'session' not found`
   - **Fix**: Session fixture now available
   - **Tests**: Default values for `is_active` and timestamps

3. **test_repr**:
   - **Current error**: `fixture 'session' not found`
   - **Fix**: Session fixture now available
   - **Tests**: String representation of model

#### TestPromptTemplateValidation (3 tests)
4. **test_version_validation_positive**:
   - **Current error**: `fixture 'session' not found`
   - **Fix**: Session fixture now available
   - **Tests**: Version must be positive integer

5. **test_version_validation_zero**:
   - **Current error**: `fixture 'session' not found`
   - **Fix**: Session fixture now available
   - **Tests**: Version=0 should fail validation

6. **test_version_validation_negative**:
   - **Current error**: `fixture 'session' not found`
   - **Fix**: Session fixture now available
   - **Tests**: Negative version should fail validation

#### TestPromptTemplateConstraints (4 tests)
7. **test_unique_constraint**:
   - **Current error**: `fixture 'session' not found`
   - **Fix**: Session fixture now available
   - **Tests**: Unique constraint on (function_tag, version)

8. **test_function_tag_required**:
   - **Current error**: `fixture 'session' not found`
   - **Fix**: Session fixture now available
   - **Tests**: function_tag is required field

9. **test_template_content_required**:
   - **Current error**: `fixture 'session' not found`
   - **Fix**: Session fixture now available
   - **Tests**: template_content is required field

10. **test_check_constraint_version_positive**:
    - **Current error**: `fixture 'session' not found`
    - **Fix**: Session fixture now available
    - **Tests**: Database check constraint enforces version > 0

#### TestPromptTemplateQueries (5 tests)
11. **test_query_by_function_tag**:
    - **Current error**: `fixture 'session' not found`
    - **Fix**: Session and sample_templates fixtures now available
    - **Tests**: Querying templates by function_tag

12. **test_query_active_template**:
    - **Current error**: `fixture 'session' not found`
    - **Fix**: Session and sample_templates fixtures now available
    - **Tests**: Filtering for is_active=True templates

13. **test_query_specific_version**:
    - **Current error**: `fixture 'session' not found`
    - **Fix**: Session and sample_templates fixtures now available
    - **Tests**: Querying specific version of template

14. **test_query_no_results**:
    - **Current error**: `fixture 'session' not found`
    - **Fix**: Session and sample_templates fixtures now available
    - **Tests**: Query returning empty result set

15. **test_query_multiple_functions**:
    - **Current error**: `fixture 'session' not found`
    - **Fix**: Session and sample_templates fixtures now available
    - **Tests**: Multiple function_tags in database

#### TestPromptTemplateLangChainCompatibility (2 tests)
16. **test_langchain_template_loading**:
    - **Current error**: `fixture 'session' not found`
    - **Fix**: Session fixture now available
    - **Tests**: Template content compatible with LangChain

17. **test_langchain_template_with_multiple_variables**:
    - **Current error**: `fixture 'session' not found`
    - **Fix**: Session fixture now available
    - **Tests**: Multiple variables in template string

#### TestPromptTemplateUpdates (2 tests)
18. **test_update_template_content**:
    - **Current error**: `fixture 'session' not found`
    - **Fix**: Session fixture now available
    - **Tests**: Updating template_content field

19. **test_toggle_active_status**:
    - **Current error**: `fixture 'session' not found`
    - **Fix**: Session fixture now available
    - **Tests**: Toggling is_active flag

### Testing Approach

For all tests:
- **No test code changes needed**: Tests already request `session` parameter
- **Fixture availability**: Session fixture from conftest.py now provides what tests need
- **Database isolation**: Each test gets clean in-memory SQLite database
- **Verification**: All 19 tests should transition from ERROR to PASS

## Dependencies and Sequencing

### Must Complete Before:
- **T01**: Test Infrastructure & Database Fixtures
  - **CRITICAL**: This ticket depends entirely on T01 being complete
  - Reason: Needs `tests/conftest.py` with `session` fixture

### Must Complete Before Starting:
- T01 must be merged to main/master branch
- Cannot start T04 until T01 is fully merged

### Blocks If Not Done:
- None (T02, T03, T05 are independent)

### Sequencing Notes:
- **Hard dependency on T01** - cannot proceed until T01 is complete
- Can run in parallel with T02, T03, T05 once T01 is merged
- Low risk of merge conflicts (single test file)
- Recommended: Merge immediately after T01, before or alongside other tickets

## Clarifications and Assumptions

### Assumptions Made:

1. **Session Fixture Availability**: Assuming T01 successfully created `tests/conftest.py` with working `session` fixture
   - **BLOCKER**: Cannot proceed if T01 is incomplete
   - Verification: `pytest --fixtures tests/ | grep session`

2. **PromptTemplate Model is Mapped**: Assuming model is properly registered with SQLAlchemy Base
   - May need to verify import in conftest.py
   - Check `psychrag.data.models.__init__.py` exports the model

3. **SQLite Compatibility**: Assuming PromptTemplate model works with SQLite
   - Most SQLAlchemy models are compatible
   - May encounter issues with Postgres-specific types (JSON, ARRAY)
   - **Mitigation**: Document issues, don't modify production code

4. **sample_templates Fixture Exists**: Assuming fixture is defined somewhere in test file
   - If not, will need to create it
   - Pattern based on standard pytest fixture patterns

5. **Test Logic is Correct**: Assuming existing test assertions and logic are correct
   - Only fixing fixture availability, not test correctness
   - Any logic errors will be apparent once tests run

### Questions for Product Owner (Non-blocking):

- **Q1**: Should we eventually migrate to test Postgres containers for higher fidelity?
  - **Current approach**: SQLite per PRD (faster, simpler)
  - **Recommendation**: Revisit if SQLite compatibility issues arise

- **Q2**: Are there integration tests needed for PromptTemplate beyond unit tests?
  - **Current approach**: Unit tests only per PRD scope
  - **Recommendation**: Defer integration tests to future ticket

### Blocking Questions (Must Answer Before Implementing):

- **BLOCKER 1**: Is T01 complete and merged?
  - **How to check**: `git log --oneline | grep "T01"` or check PR status
  - **Impact**: Cannot proceed without session fixture from conftest.py
  - **ACTION**: Verify T01 is merged before starting this ticket

- **BLOCKER 2**: Where is the PromptTemplate model defined?
  - **How to check**: `find src -name "*prompt_template*.py" -o -name "*template*.py"`
  - **Impact**: Need correct import path for conftest.py
  - **ACTION**: Locate model file and verify import path

### Implementer Notes:

> **Before implementing**:
> 1. **VERIFY T01 IS COMPLETE**: Check that `tests/conftest.py` exists with `session` fixture
> 2. Locate PromptTemplate model file and verify import path
> 3. Run `pytest --fixtures tests/` to confirm session fixture is available
> 4. Read `test_prompt_template_model.py` to understand sample_templates fixture requirements
>
> **Implementation strategy**:
> 1. First, just try running the tests: `pytest tests/unit/test_prompt_template_model.py -v`
> 2. If fixture error is gone but tests fail, analyze specific failures
> 3. If sample_templates fixture is missing, create it based on test requirements
> 4. If model import issues, add explicit import to conftest.py
> 5. If SQLite compatibility issues, document them (don't modify production code)
>
> **Common issues and solutions**:
> - **"table does not exist"**: Model not registered with Base, add import to conftest.py
> - **"unique constraint violation"**: sample_templates using duplicate (function_tag, version)
> - **"check constraint failed"**: version <= 0, ensure version >= 1 in fixtures
> - **"column not found"**: Field name mismatch, check model definition

## Manual Test Plan (Acceptance Criteria)

Run these commands in sequence to verify completion:

```bash
# 0. PREREQUISITE: Verify T01 is complete
pytest --fixtures tests/ | grep -A 3 "session"
# Expected: session fixture appears with description
# If not found: T01 is not complete, cannot proceed

# 1. Run test_prompt_template_model.py
pytest tests/unit/test_prompt_template_model.py -v
# Expected: 19 tests run (no "fixture 'session' not found" errors)
# Expected: All 19 PASSED
# Previously: 19 errors, 0 tests ran

# 2. Verify specific test classes
pytest tests/unit/test_prompt_template_model.py::TestPromptTemplateCreation -v
# Expected: 3 passed (was 3 errors)

pytest tests/unit/test_prompt_template_model.py::TestPromptTemplateQueries -v
# Expected: 5 passed (was 5 errors)

# 3. Verify sample_templates fixture works
pytest tests/unit/test_prompt_template_model.py::TestPromptTemplateQueries::test_query_by_function_tag -v
# Expected: PASSED (this test uses sample_templates)

# 4. Verify database isolation (run tests multiple times)
pytest tests/unit/test_prompt_template_model.py::TestPromptTemplateConstraints::test_unique_constraint -v
pytest tests/unit/test_prompt_template_model.py::TestPromptTemplateConstraints::test_unique_constraint -v
pytest tests/unit/test_prompt_template_model.py::TestPromptTemplateConstraints::test_unique_constraint -v
# Expected: All 3 runs PASSED (no unique constraint violations from previous runs)

# 5. Check for "fixture not found" errors are gone
pytest tests/unit/test_prompt_template_model.py 2>&1 | grep "fixture 'session' not found"
# Expected: No output (error should be gone)

# 6. Run full test suite and check progress
pytest tests/unit/ --tb=no -q | tail -1
# Expected: "199 passed, 10 failed" (assuming T02+T03 complete: 180 + 19 = 199)
# Or: "177 passed, 24 failed" (if only T01+T04: 158 + 19 = 177)

# 7. Verify no regressions
pytest tests/unit/test_api_endpoints.py -v
# Expected: All baseline tests still pass

# 8. Quick syntax check
python -m py_compile tests/unit/test_prompt_template_model.py
# Expected: No syntax errors
```

**Success Criteria**:
- All 8 verification steps pass
- 19 additional tests pass (177-199 total depending on T02/T03 status)
- No "fixture 'session' not found" errors
- Database isolation working (multiple test runs don't interfere)
- Ready to proceed with T05 (inspection and cleanup)
