# PRD: Test Suite Compatibility Fixes

---
status: draft
owner: TODO
created: 2025-12-04
slug: test-suite-fixes
---

## 1. Summary

The current test suite has 51 failing tests (32 failures, 19 errors) across multiple modules due to module evolution that outpaced test updates. This PRD outlines a systematic approach to align tests with current module implementations **without modifying production code**, ensuring the test suite accurately reflects actual system behavior while maintaining code coverage and test quality.

## 2. Problem & Context

### Current Situation
The pytest run shows significant test failures across 6 test modules:
- **test_conv_pdf2md.py**: 6 failures (return value mismatches, new parameters)
- **test_conversion_api_endpoints.py**: 11 failures (missing async support)
- **test_database.py**: 1 failure (environment variable handling)
- **test_inspection.py**: 3 failures (file availability logic)
- **test_llm_citation_parser.py**: 6 failures (missing function references)
- **test_original_markdown.py**: 5 failures (missing async support)
- **test_prompt_template_model.py**: 19 errors (missing fixtures)

### Root Causes
1. **Module Evolution**: Production code added new parameters (`hierarchical`, `compare`, `use_gpu`) and changed return types (tuple vs string) without test updates
2. **Refactoring**: LLM citation parser was refactored, removing `create_langchain_chat` function
3. **Async Migration**: API endpoints became async but tests remained synchronous
4. **Missing Infrastructure**: No shared `conftest.py` with database fixtures for all test modules

### Impact
- 158 tests passing (76% pass rate)
- Reduced confidence in test coverage
- CI/CD pipeline failures
- Slower development velocity due to unclear test expectations

## 3. Goals & Non-Goals

### 3.1 Goals
- **G1**: Achieve 100% test pass rate (0 failures, 0 errors)
- **G2**: Update tests to reflect actual module behavior without changing production code
- **G3**: Add missing test infrastructure (async support, fixtures)
- **G4**: Remove obsolete tests for refactored-out functionality
- **G5**: Maintain or improve test coverage percentage
- **G6**: Document test patterns for future maintainability

### 3.2 Non-Goals
- **NG1**: Modifying production module code to fix tests (except where explicitly unavoidable)
- **NG2**: Adding new features or functionality
- **NG3**: Refactoring production code architecture
- **NG4**: Performance optimization of tests or production code
- **NG5**: Fixing the database environment variable issue (test_database.py::test_admin_database_url) - deferred to separate ticket

## 4. Users & Use Cases

### 4.1 User Segments
- **Primary**: Development team running tests locally and in CI/CD
- **Secondary**: Future contributors onboarding to the codebase

### 4.2 Key Use Cases / User Stories
- **UC1**: As a developer, I want to run `pytest` and see all tests pass so I can confidently merge code
- **UC2**: As a CI/CD system, I need reliable tests to validate pull requests automatically
- **UC3**: As a new contributor, I want clear test patterns to follow when adding new tests
- **UC4**: As a maintainer, I want tests that accurately document expected module behavior

## 5. Requirements

### 5.1 Functional Requirements

#### Phase 1: Infrastructure & Dependencies (Critical)
- **FR1.1**: Add `pytest-asyncio` to `[project.optional-dependencies].dev` in pyproject.toml
- **FR1.2**: Create `tests/conftest.py` with shared database fixtures (session, engine, Base)
- **FR1.3**: Configure pytest-asyncio mode in `[tool.pytest.ini_options]`

#### Phase 2: Async Test Support (High Priority - 16 failures)
- **FR2.1**: Add `@pytest.mark.asyncio` decorators to all async test functions in:
  - `test_conversion_api_endpoints.py` (11 tests)
  - `test_original_markdown.py` (5 tests)
- **FR2.2**: Ensure async fixtures properly handle `async with get_session()` context managers
- **FR2.3**: Verify mock configurations work with async/await patterns

#### Phase 3: PDF Conversion Tests (High Priority - 6 failures)
- **FR3.1**: Update `test_conv_pdf2md.py` to handle tuple return values when `compare=True`
- **FR3.2**: Add `hierarchical=True, compare=True, use_gpu=True` to expected call arguments
- **FR3.3**: Update `test_successful_conversion` to expect `(str, str)` tuple
- **FR3.4**: Update `test_output_file_created` to verify both `.style.md` and `.hier.md` files
- **FR3.5**: Update `test_path_object_input` to handle tuple return
- **FR3.6**: Update `main()` tests to handle compare mode (tuple unpacking in stdout)

#### Phase 4: Prompt Template Tests (High Priority - 19 errors)
- **FR4.1**: Add `session` fixture to `tests/conftest.py` using SQLAlchemy test patterns
- **FR4.2**: Configure in-memory SQLite database for test isolation
- **FR4.3**: Implement `Base.metadata.create_all()` in fixture setup
- **FR4.4**: Implement `Base.metadata.drop_all()` in fixture teardown
- **FR4.5**: Ensure `sample_templates` fixture depends on `session` fixture

#### Phase 5: Inspection Logic Tests (Medium Priority - 3 failures)
- **FR5.1**: Update `test_no_files_present` mock to return `available=True` for files the inspection logic considers available
- **FR5.2**: Update `test_some_files_present` expectations to match actual `get_conversion_inspection()` behavior
- **FR5.3**: Update `test_style_hier_requires_both_files` to match current inspection logic (appears to check existence differently)
- **FR5.4**: Review actual `inspection.py` logic (lines 119-130) to understand file checking behavior

#### Phase 6: LLM Citation Parser Tests (Low Priority - 6 failures)
- **FR6.1**: Remove all 6 tests in `test_llm_citation_parser.py`:
  - `test_parse_apa_citation_success`
  - `test_parse_mla_citation_success`
  - `test_parse_handles_partial_data`
  - `test_parse_llm_error_wrapped`
  - `test_parse_chicago_citation`
  - `test_parse_journal_article_with_doi`
- **FR6.2**: Add comment explaining removal: "Tests removed as create_langchain_chat was refactored out in module restructuring"
- **FR6.3**: Consider adding TODO for future citation parser tests if functionality still exists

#### Phase 7: Documentation & Cleanup (Post-completion)
- **FR7.1**: Document test fixture patterns in `tests/README.md`
- **FR7.2**: Add docstring examples showing async test patterns
- **FR7.3**: Document compare mode testing strategy for PDF conversion
- **FR7.4**: Create GitHub issue for deferred `test_admin_database_url` fix

### 5.2 Non-Functional Requirements
- **NFR1**: All test updates must maintain existing test intent (test the same behavior, just correctly)
- **NFR2**: Test execution time should not increase by more than 10%
- **NFR3**: Test code should follow existing pytest conventions and style
- **NFR4**: Mock usage should be minimal and well-documented
- **NFR5**: Fixture reuse should be maximized across test modules

## 6. UX / UI Notes
Not applicable - this is internal test infrastructure work.

## 7. Analytics & Success Metrics

### Success Metrics
- **KPI1**: Test pass rate = 100% (currently 76%)
- **KPI2**: Test execution completes without errors (currently 19 errors)
- **KPI3**: Code coverage maintained or improved (baseline: measure before fixes)
- **KPI4**: CI/CD pipeline green status

### Tracking Points
- Before: 158 passed, 32 failed, 19 errors
- After: Target 209 passed, 0 failed, 0 errors (minus 6 removed tests = 203 passed)

## 8. Dependencies & Risks

### Dependencies
- **D1**: pytest-asyncio package (requires pyproject.toml update)
- **D2**: Understanding of actual `convert_pdf_to_markdown` behavior (documented in conv_pdf2md.py:103-111)
- **D3**: Access to inspection.py logic (already reviewed)
- **D4**: SQLAlchemy test database patterns (standard practice)

### Risks & Mitigation
- **R1**: Test updates might reveal actual bugs in production code
  - *Mitigation*: Flag any suspected bugs for separate review; don't modify production code per constraint
- **R2**: Async test patterns might have subtle timing issues
  - *Mitigation*: Use proven pytest-asyncio patterns; add explicit async fixture handling
- **R3**: Database fixtures might conflict with existing test isolation
  - *Mitigation*: Use transaction rollback pattern; ensure each test gets clean state
- **R4**: Removing LLM parser tests might reduce coverage
  - *Mitigation*: Document removal reason; add TODO for replacement tests if functionality exists elsewhere

## 9. Rollout & Milestones

### Phase 1: Infrastructure (Day 1 - ~2 hours)
- Add pytest-asyncio dependency
- Create tests/conftest.py with database fixtures
- Verify fixture availability across all test modules

### Phase 2: High-Priority Fixes (Day 1-2 - ~4 hours)
- Fix async test decorators (16 tests)
- Fix PDF conversion tests (6 tests)
- Fix prompt template fixture errors (19 tests)
- **Checkpoint**: 41 failures/errors resolved

### Phase 3: Medium/Low Priority (Day 2 - ~2 hours)
- Fix inspection logic tests (3 tests)
- Remove LLM parser tests (6 tests)
- **Checkpoint**: All failures/errors resolved

### Phase 4: Documentation & Cleanup (Day 2-3 - ~1 hour)
- Document patterns in tests/README.md
- Create deferred ticket for test_admin_database_url
- Final test run verification

### Total Effort Estimate
- **Development**: 8-9 hours
- **Review/Testing**: 2-3 hours
- **Total**: 10-12 hours (1.5-2 days)

## 10. Open Questions

1. ~~Should we add pytest-asyncio to main dependencies or dev dependencies?~~
   - **Answer**: Dev dependencies per user confirmation

2. ~~Should we update tests to match module behavior or fix modules to match tests?~~
   - **Answer**: Update tests per PRD constraint (no production code changes)

3. ~~What to do about LLM citation parser tests referencing removed function?~~
   - **Answer**: Remove tests per user confirmation

4. ~~Is the inspection logic behavior (marking files as available when mocked to not exist) correct or a bug?~~
   - **Answer**: Update tests to match current logic per user confirmation

5. **OPEN**: Should we create integration tests for compare mode PDF conversion scenarios?
   - Current tests are unit tests with mocks; consider E2E tests with real small PDFs

6. **OPEN**: Should tests/conftest.py use in-memory SQLite or match production Postgres for compatibility?
   - Recommendation: SQLite for speed, but document any dialect differences

7. **OPEN**: What is the expected behavior for `test_admin_database_url` environment variable handling?
   - Deferred to separate ticket per user confirmation

---

## Appendix A: Test Failure Breakdown

### By Category
1. **Async Support**: 16 failures (test_conversion_api_endpoints.py, test_original_markdown.py)
2. **Return Type Changes**: 6 failures (test_conv_pdf2md.py)
3. **Missing Fixtures**: 19 errors (test_prompt_template_model.py)
4. **Logic Mismatches**: 3 failures (test_inspection.py)
5. **Refactored Functions**: 6 failures (test_llm_citation_parser.py)
6. **Environment Variables**: 1 failure (test_database.py - deferred)

### Test File Priority
1. **Critical**: test_prompt_template_model.py (19 errors blocking all tests)
2. **High**: test_conversion_api_endpoints.py (11 failures), test_conv_pdf2md.py (6 failures)
3. **Medium**: test_inspection.py (3 failures), test_original_markdown.py (5 failures)
4. **Low**: test_llm_citation_parser.py (6 failures - will be removed)
5. **Deferred**: test_database.py (1 failure - separate ticket)

## Appendix B: Example Fixture Implementation

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from psychrag.data.models import Base

@pytest.fixture(scope="function")
def engine():
    """Create in-memory SQLite engine for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def session(engine) -> Session:
    """Create database session for tests with automatic rollback."""
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()
```

## Appendix C: Example Async Test Pattern

```python
# Example from test_conversion_api_endpoints.py
import pytest

@pytest.mark.asyncio
async def test_get_style_file_success(self, mock_exists, mock_read_text, ...):
    """Test successful retrieval of style.md file."""
    # Test implementation remains the same
    result = await get_file_content(io_file_id=1, file_type="style")
    assert result.content == "# Test Content"
```
