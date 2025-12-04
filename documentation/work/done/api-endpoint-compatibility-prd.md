# Product Requirements Document: Test Suite Alignment with API Implementation

## Overview
This PRD addresses test failures identified in `tests/unit/test_api_endpoints.py` by aligning tests with the actual API implementation. The approach is to update tests to match existing API behavior rather than modifying the API to match outdated test expectations.

## Problem Statement
Test results show 13 failing tests out of 27 total tests. The failures fall into three categories:

1. **Settings Router** (3 failures): Response format mismatch - tests expect legacy format, API returns structured config
2. **Chunking Router** (5 failures): Tests for legacy endpoints that don't exist in current API
3. **RAG Router** (5 failures): Tests for legacy endpoints that don't exist in current API

**Key Principle**: Tests should reflect the actual API implementation, not legacy expectations. The API implementation is correct and should not be changed.

## Requirements

### 1. Settings Router Test Updates

#### 1.1 Response Format Test Update
**Current API Behavior**: `GET /settings/` returns `AppConfigSchema` with keys: `database`, `llm`, `paths`

**Current Test Expectation**: Test expects response with `settings` key containing a dictionary

**Solution**: Update test to match actual API response format.

**Test Changes Required**:
- Update `test_get_all_settings()` to assert presence of `database`, `llm`, and `paths` keys
- Remove assertion for `settings` key
- Verify response structure matches `AppConfigSchema`:
  ```python
  assert "database" in data
  assert "llm" in data
  assert "paths" in data
  assert isinstance(data["database"], dict)
  assert isinstance(data["llm"], dict)
  assert isinstance(data["paths"], dict)
  ```

#### 1.2 Remove Legacy Settings Endpoint Tests
**Missing Endpoints** (not implemented in API):
- `GET /settings/{key}` - Get specific setting by key
- `PUT /settings/{key}` - Update specific setting by key

**Solution**: Remove tests for these endpoints as they don't exist in the current API.

**Test Changes Required**:
- Remove `test_get_specific_setting()` method
- Remove `test_update_setting()` method
- Keep `test_get_nonexistent_setting()` if it tests 404 behavior for non-existent endpoints (or remove if it's testing the missing endpoint)

**Note**: The current API provides structured endpoints:
- `GET /settings/database` - Get database configuration
- `PUT /settings/database` - Update database configuration
- `GET /settings/llm` - Get LLM configuration
- `PUT /settings/llm` - Update LLM configuration
- `GET /settings/paths` - Get paths configuration
- `PUT /settings/paths` - Update paths configuration

These endpoints are correctly implemented and should remain unchanged.

### 2. Chunking Router Test Removal

#### 2.1 Remove Tests for Non-Existent Endpoints
The following legacy endpoints are tested but don't exist in the current API:
- `POST /chunk/headings` - Heading-based chunking
- `POST /chunk/content` - Content-based chunking  
- `POST /chunk/suggest` - Chunk suggestions
- `POST /chunk/extract-bib` - Bibliography extraction
- `POST /chunk/process-llm` - LLM processing

**Current API Implementation**: Uses work-based endpoints:
- `POST /chunk/work/{work_id}/apply-heading-chunks` - Apply heading chunking
- `POST /chunk/work/{work_id}/apply-content-chunks` - Apply content chunking
- `GET /chunk/works` - List works with sanitized files
- `GET /chunk/work/{work_id}` - Get work detail
- And other work-based endpoints documented in the router

**Solution**: Remove tests for legacy endpoints that don't exist.

**Test Changes Required**:
- Remove `test_chunk_by_headings()` method
- Remove `test_chunk_by_content()` method
- Remove `test_suggest_chunks()` method
- Remove `test_extract_bibliography()` method
- Remove `test_process_llm()` method

**Note**: The current API correctly uses work-based endpoints which provide better structure and context. These endpoints should remain unchanged. If tests are needed for chunking functionality, they should test the actual work-based endpoints instead.

### 3. RAG Router Test Removal

#### 3.1 Remove Tests for Non-Existent Endpoints
The following legacy endpoints are tested but don't exist in the current API:
- `POST /rag/query` - Full RAG query
- `POST /rag/retrieve` - Chunk retrieval
- `POST /rag/expand-query` - Query expansion
- `POST /rag/augment` - Content augmentation
- `POST /rag/generate` - Response generation

**Current API Implementation**: Uses query-based endpoints:
- `GET /rag/queries` - List all queries
- `GET /rag/queries/{id}` - Get query details
- `POST /rag/queries/{id}/embed` - Run vectorization
- `POST /rag/queries/{id}/retrieve` - Run retrieval
- `POST /rag/queries/{id}/consolidate` - Run consolidation
- `POST /rag/expansion/prompt` - Generate expansion prompt
- `POST /rag/expansion/run` - Run full expansion with LLM
- `POST /rag/expansion/manual` - Parse & save manual expansion response
- And other query-based endpoints documented in the router

**Solution**: Remove tests for legacy endpoints that don't exist.

**Test Changes Required**:
- Remove `test_rag_query()` method
- Remove `test_retrieve_chunks()` method
- Remove `test_expand_query()` method
- Remove `test_augment_content()` method
- Remove `test_generate_response()` method

**Note**: The current API correctly uses a query-based workflow which provides better state management and tracking. These endpoints should remain unchanged. If tests are needed for RAG functionality, they should test the actual query-based endpoints instead.

## Non-Functional Requirements

### API Stability
- **CRITICAL**: No changes to existing API endpoints or response formats
- All existing endpoints must continue to work exactly as before
- Existing API consumers should see no changes in behavior

### Test Accuracy
- Tests must accurately reflect the actual API implementation
- Test assertions should match actual API response schemas
- Error responses should follow FastAPI standard format (already implemented)

### Test Coverage
- Tests should cover all implemented endpoints
- Removed tests reduce false negatives and improve test suite reliability
- Consider adding tests for actual implemented endpoints if coverage gaps exist

## Implementation Plan

### Phase 1: Settings Router Test Updates (Priority: High)
1. Update `test_get_all_settings()` to assert `database`, `llm`, `paths` keys instead of `settings` key
2. Remove `test_get_specific_setting()` method (endpoint doesn't exist)
3. Remove `test_update_setting()` method (endpoint doesn't exist)
4. Review `test_get_nonexistent_setting()` - remove if testing non-existent endpoint, keep if testing 404 behavior
5. Verify tests pass with actual API response format

### Phase 2: Chunking Router Test Removal (Priority: High)
1. Remove `test_chunk_by_headings()` method
2. Remove `test_chunk_by_content()` method
3. Remove `test_suggest_chunks()` method
4. Remove `test_extract_bibliography()` method
5. Remove `test_process_llm()` method
6. Verify remaining tests pass

### Phase 3: RAG Router Test Removal (Priority: High)
1. Remove `test_rag_query()` method
2. Remove `test_retrieve_chunks()` method
3. Remove `test_expand_query()` method
4. Remove `test_augment_content()` method
5. Remove `test_generate_response()` method
6. Verify remaining tests pass

### Phase 4: Testing & Validation (Priority: Critical)
1. Run full test suite: `pytest tests/unit/test_api_endpoints.py -v`
2. Verify all remaining tests pass (expected: 14 tests after removals)
3. Verify no regressions in existing functionality
4. Consider adding tests for actual implemented endpoints if coverage gaps exist
5. Update test documentation if needed

## Success Criteria
- ✅ All remaining tests in `test_api_endpoints.py` pass (after removals and updates)
- ✅ No changes to existing API endpoints or response formats
- ✅ Tests accurately reflect actual API implementation
- ✅ Test suite is reliable and free of false negatives
- ✅ Removed tests were for non-existent endpoints
- ✅ Updated tests match actual API response schemas

## Risks & Mitigation

### Risk 1: Test Coverage Reduction
**Risk**: Removing tests may reduce coverage of API functionality
**Mitigation**: 
- Review actual implemented endpoints to ensure adequate coverage
- Consider adding tests for work-based chunking endpoints if needed
- Consider adding tests for query-based RAG endpoints if needed
- Verify OpenAPI schema documents all endpoints correctly

### Risk 2: Test Assertion Accuracy
**Risk**: Updated test assertions may not fully validate API response structure
**Mitigation**:
- Review `AppConfigSchema` structure carefully
- Verify all required fields are asserted in updated tests
- Use actual API response schemas as reference
- Test with real API responses to validate assertions

### Risk 3: Missing Test Cases
**Risk**: Some implemented endpoints may lack test coverage
**Mitigation**:
- Audit actual API endpoints against test coverage
- Add tests for critical endpoints that are missing coverage
- Prioritize tests for endpoints used by UI or external consumers

## Dependencies
- Existing API implementation (no changes required)
- Test file: `tests/unit/test_api_endpoints.py`
- API schemas: `psychrag_api.schemas` modules for reference
- Current router implementations for understanding actual endpoints

## Notes
- This PRD focuses on aligning tests with actual API implementation
- No API code changes are required - only test file modifications
- The API implementation is correct and follows modern REST patterns
- Work-based and query-based endpoints provide better structure than legacy file-path-based endpoints
- Removing tests for non-existent endpoints improves test suite reliability
- Updated tests should accurately reflect the actual API contract

