# T01 Fix Settings Router Tests

## Context

- Link back to the PRD: @documentation/api-endpoint-compatibility-prd.md
- Specific section: **1. Settings Router Test Updates** (sections 1.1 and 1.2)
- The Settings Router tests currently expect legacy response formats and test endpoints that don't exist. This ticket updates tests to match the actual API implementation, which returns structured configuration objects (`AppConfigSchema`) rather than a flat settings dictionary.

## Outcome

When this ticket is complete:
- `test_get_all_settings()` correctly validates the actual API response format with `database`, `llm`, and `paths` keys
- Tests for non-existent endpoints (`GET /settings/{key}` and `PUT /settings/{key}`) are removed
- All Settings Router tests pass against the actual API implementation
- Test suite accurately reflects the API contract without false negatives

## Scope

- **In scope:**
  - Update `test_get_all_settings()` to assert correct response structure (`database`, `llm`, `paths` keys)
  - Remove `test_get_specific_setting()` method (endpoint doesn't exist)
  - Remove `test_update_setting()` method (endpoint doesn't exist)
  - Review and potentially update `test_get_nonexistent_setting()` based on actual API behavior
  - Verify all Settings Router tests pass

- **Out of scope:**
  - Changes to API implementation (API code remains unchanged)
  - Adding new endpoints
  - Tests for other routers (handled in T02 and T03)

## Implementation plan

### Test File Updates

1. **Update `test_get_all_settings()` method** in `tests/unit/test_api_endpoints.py`:
   - Remove assertion: `assert "settings" in data`
   - Remove assertion: `assert isinstance(data["settings"], dict)`
   - Add assertions for actual API response structure:
     ```python
     assert "database" in data
     assert "llm" in data
     assert "paths" in data
     assert isinstance(data["database"], dict)
     assert isinstance(data["llm"], dict)
     assert isinstance(data["paths"], dict)
     ```
   - Optionally add assertions for nested structure validation:
     - Verify `database` contains expected keys: `admin_user`, `host`, `port`, `db_name`, `app_user`
     - Verify `llm` contains expected keys: `provider`, `models`
     - Verify `paths` contains expected keys: `input_dir`, `output_dir`

2. **Remove `test_get_specific_setting()` method**:
   - Delete the entire method (lines 82-88)
   - This endpoint (`GET /settings/{key}`) does not exist in the API

3. **Remove `test_update_setting()` method**:
   - Delete the entire method (lines 95-104)
   - This endpoint (`PUT /settings/{key}`) does not exist in the API

4. **Review `test_get_nonexistent_setting()` method**:
   - Current test calls `GET /settings/nonexistent_key` and expects 404
   - Verify this endpoint actually returns 404 (it should, as the endpoint doesn't exist)
   - If the endpoint doesn't exist, FastAPI should return 404 automatically
   - Keep the test if it validates 404 behavior correctly, or remove if redundant

### Verification Steps

1. Run Settings Router tests: `pytest tests/unit/test_api_endpoints.py::TestSettingsRouter -v`
2. Verify all tests pass
3. Verify no regressions in other test classes

## Unit tests

Since this ticket is about fixing existing tests, the unit tests themselves are what we're updating. However, verify:

- **Test execution:**
  - Run `pytest tests/unit/test_api_endpoints.py::TestSettingsRouter -v`
  - All tests in `TestSettingsRouter` class should pass
  - No warnings or errors should appear

- **Test assertions:**
  - `test_get_all_settings()` validates the complete `AppConfigSchema` structure
  - Response structure matches `src/psychrag_api/schemas/settings.AppConfigSchema`
  - All required top-level keys are present and have correct types

- **Test coverage:**
  - Verify that removed tests were indeed for non-existent endpoints
  - Confirm remaining tests cover the actual API endpoints:
    - `GET /settings/` (tested by `test_get_all_settings`)
    - `GET /settings/database` (may need new test if not covered)
    - `PUT /settings/database` (may need new test if not covered)
    - `GET /settings/llm` (may need new test if not covered)
    - `PUT /settings/llm` (may need new test if not covered)
    - `GET /settings/paths` (may need new test if not covered)
    - `PUT /settings/paths` (may need new test if not covered)

## Dependencies and sequencing

- **No dependencies:** This ticket can be implemented independently
- **Can be done in parallel with:** T02 and T03 (they modify different test classes)
- **Should be done before:** Any future tickets that add tests for Settings Router endpoints

## Manual test plan

1. **Verify API response format:**
   ```bash
   # Start API server (if not running)
   # Make request to GET /settings/
   curl http://localhost:8000/settings/
   ```
   - Verify response contains `database`, `llm`, `paths` keys
   - Verify response does NOT contain `settings` key
   - Verify nested structure matches `AppConfigSchema`

2. **Verify non-existent endpoints return 404:**
   ```bash
   curl http://localhost:8000/settings/embedding_model
   curl http://localhost:8000/settings/chunk_size
   ```
   - Both should return 404 Not Found

3. **Run test suite:**
   ```bash
   venv\Scripts\pytest tests/unit/test_api_endpoints.py::TestSettingsRouter -v
   ```
   - All tests should pass
   - No warnings about deprecated endpoints

## Clarifications and assumptions

### Assumptions
- The API endpoint `GET /settings/` returns `AppConfigSchema` as documented
- FastAPI automatically returns 404 for non-existent routes
- The `test_get_nonexistent_setting()` test is testing a non-existent endpoint path, which should return 404

### Open Questions
- **Q1:** Should we add tests for the actual structured endpoints (`GET /settings/database`, `GET /settings/llm`, `GET /settings/paths`)? 
  - **Assumption:** Not required for this ticket, but could be added in a follow-up if coverage is needed
- **Q2:** Should `test_get_nonexistent_setting()` be kept or removed?
  - **Assumption:** Keep it if it validates 404 behavior for non-existent paths, remove if it's redundant

> **Before implementing:** Review the actual API response from `GET /settings/` to confirm the exact structure. Verify that `AppConfigSchema` matches what the API actually returns. If there are any discrepancies between the schema and actual response, update the test assertions accordingly.

