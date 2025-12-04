# PRD: Cleanup Unused API Endpoints

## Executive Summary
Conduct a comprehensive audit of all backend API endpoints and systematically verify their usage in the UI (`/psychrag_ui`). Remove any API endpoints that are NOT used anywhere in the UI, including their:
- Route handlers
- Schema definitions
- Unit tests
- Related business logic (if exclusively used by the unused endpoint)

## Background
The psychRAG-test project has evolved over time, and there may be API endpoints that were created but never integrated into the UI, or were deprecated when UI workflows changed. These unused endpoints add maintenance burden and complexity.

## Goals
1. **Identify** all API endpoints defined in the backend
2. **Verify** usage of each endpoint in the UI codebase
3. **Remove** endpoints with zero UI usage
4. **Document** findings and removals

## Non-Goals
- Removing endpoints used by CLI tools or backend-only workflows
- Refactoring or optimizing endpoints that ARE used
- Making changes to the UI

---

## API Inventory & Analysis

### Router: Init (`/init`)
**File:** `src/psychrag_api/routers/init.py`

| Endpoint | Method | Status | UI Usage |
|----------|--------|--------|----------|
| `/init/database` | POST | ✅ USED | `settings/page.tsx:155` |
| `/init/db-health` | GET | ✅ USED | `settings/page.tsx:137` |

**Summary:** All endpoints USED. No removals needed.

---

### Router: Settings (`/settings`)
**File:** `src/psychrag_api/routers/settings.py`

| Endpoint | Method | Status | UI Usage |
|----------|--------|--------|----------|
| `/settings/` | GET | ✅ USED | `settings/page.tsx:115` |
| `/settings/database` | PUT | ✅ USED | `settings/page.tsx:181` |
| `/settings/llm` | PUT | ✅ USED | `settings/page.tsx:207` |
| `/settings/paths` | PUT | ✅ USED | `settings/page.tsx:254` |
| `/settings/templates/` | GET | ✅ USED | `components/settings/templates-tab.tsx:53` |
| `/settings/templates/{function_tag}` | GET | ✅ USED | `settings/templates/[function_tag]/page.tsx:85` |
| `/settings/templates/{function_tag}` | POST | ✅ USED | `settings/templates/[function_tag]/page.tsx:117` |
| `/settings/templates/{function_tag}` | PUT | ✅ USED | `settings/templates/[function_tag]/page.tsx:145` |
| `/settings/templates/{function_tag}/reset` | POST | ✅ USED | `settings/templates/[function_tag]/page.tsx:190` |

**Summary:** All endpoints USED. No removals needed.

---

### Router: Templates (`/settings/templates`)
**File:** `src/psychrag_api/routers/templates.py`

| Endpoint | Method | Status | UI Usage |
|----------|--------|--------|----------|
| All endpoints | - | ✅ USED | Part of settings router, all used |

**Summary:** All endpoints USED. No removals needed.

---

### Router: Conversion (`/conv`)
**File:** `src/psychrag_api/routers/conversion.py`

| Endpoint | Method | Status | UI Usage | Notes |
|----------|--------|--------|----------|-------|
| `/conv/formats` | GET | ❌ UNUSED | None | Stub implementation |
| `/conv/epub` | POST | ❌ UNUSED | None | Stub with TODO |
| `/conv/pdf` | POST | ❌ UNUSED | None | Stub with TODO |
| `/conv/status/{job_id}` | GET | ❌ UNUSED | None | Stub with TODO |
| `/conv/io-folder-data` | GET | ✅ USED | `conv/page.tsx:56` | |
| `/conv/convert-file` | POST | ✅ USED | `conv/page.tsx:103` | |
| `/conv/inspection/{io_file_id}` | GET | ✅ USED | `conv/[id]/page.tsx:79` | |
| `/conv/generate-toc-titles/{io_file_id}` | POST | ✅ USED | `conv/[id]/page.tsx:133` | |
| `/conv/file-content/{io_file_id}/{file_type}` | GET | ✅ USED | `conv/[id]/inspect_style_hier/page.tsx:127,128` | |
| `/conv/file-content/{io_file_id}/{file_type}` | PUT | ✅ USED | `conv/[id]/inspect_style_hier/page.tsx:199,256` | |
| `/conv/suggestion/{io_file_id}` | GET | ✅ USED | `conv/[id]/inspect_style_hier/page.tsx:152` | |
| `/conv/select-file/{io_file_id}` | POST | ✅ USED | `conv/[id]/inspect_style_hier/page.tsx:257` | |
| `/conv/manual-prompt-toc-titles` | GET | ✅ USED | `conv/[id]/inspect_toc_titles/page.tsx:84` | |
| `/conv/readiness/{io_file_id}` | GET | ✅ USED | `conv/[id]/page.tsx:101` | |
| `/conv/add-to-database/{io_file_id}` | POST | ✅ USED | `conv/[id]/add/page.tsx:208` | |
| `/conv/parse-citation-llm` | POST | ✅ USED | `conv/[id]/add/page.tsx:670` | |
| `/conv/original-markdown/{io_file_id}` | GET | ✅ USED | `conv/[id]/inspect_original_md/page.tsx:41` | |
| `/conv/original-markdown/{io_file_id}` | PUT | ✅ USED | `conv/[id]/inspect_original_md/page.tsx:61` | |
| `/conv/delete/{io_file_id}` | DELETE | ✅ USED | `conv/[id]/page.tsx:168` | |

**UNUSED Endpoints:** 4
- `/conv/formats` (GET) - Lines 57-86
- `/conv/epub` (POST) - Lines 89-119
- `/conv/pdf` (POST) - Lines 122-152
- `/conv/status/{job_id}` (GET) - Lines 155-178

---

### Router: Sanitization (`/sanitization`)
**File:** `src/psychrag_api/routers/sanitization.py`

| Endpoint | Method | Status | UI Usage | Notes |
|----------|--------|--------|----------|-------|
| `/sanitization/works` | GET | ✅ USED | `sanitization/page.tsx:51` | |
| `/sanitization/work/{work_id}` | GET | ✅ USED | `sanitization/[id]/page.tsx:54` | |
| `/sanitization/work/{work_id}/extract-titles` | POST | ✅ USED | `sanitization/[id]/page.tsx:80` | |
| `/sanitization/work/{work_id}/suggest-title-changes` | POST | ✅ USED | `sanitization/[id]/page.tsx:127` | |
| `/sanitization/work/{work_id}/apply-title-changes` | POST | ✅ USED | `sanitization/[id]/page.tsx:166` | |
| `/sanitization/work/{work_id}/skip-apply` | POST | ✅ USED | `sanitization/[id]/page.tsx:201` | |
| `/sanitization/work/{work_id}/verify-title-changes` | POST | ❌ UNUSED | None | Implemented but not integrated |
| `/sanitization/work/{work_id}/prompt` | GET | ✅ USED | `sanitization/[id]/gen-title-changes/page.tsx:64` | |
| `/sanitization/work/{work_id}/manual-title-changes` | POST | ✅ USED | `sanitization/[id]/gen-title-changes/page.tsx:110` | |
| `/sanitization/work/{work_id}/title-changes/content` | GET | ✅ USED | `sanitization/[id]/title-changes/page.tsx:96` | |
| `/sanitization/work/{work_id}/title-changes/content` | PUT | ✅ USED | `sanitization/[id]/title-changes/page.tsx:146` | |
| `/sanitization/work/{work_id}/titles/content` | GET | ✅ USED | `sanitization/[id]/titles/page.tsx:56` | |
| `/sanitization/work/{work_id}/titles/content` | PUT | ✅ USED | `sanitization/[id]/titles/page.tsx:82` | |
| `/sanitization/add-sanitized` | POST | ✅ USED | `sanitization/add/page.tsx:120` | |
| `/sanitization/extract-toc` | POST | ❌ UNUSED | None | Legacy stub |
| `/sanitization/extract-titles` | POST | ❌ UNUSED | None | Legacy stub |
| `/sanitization/suggest-changes` | POST | ❌ UNUSED | None | Legacy stub |
| `/sanitization/apply-changes` | POST | ❌ UNUSED | None | Legacy stub |
| `/sanitization/work/{work_id}/title-changes/table` | GET | ✅ USED | `sanitization/[id]/title-changes/page.tsx:97` | |
| `/sanitization/work/{work_id}/title-changes/table` | PUT | ✅ USED | `sanitization/[id]/title-changes/page.tsx:147` | |

**UNUSED Endpoints:** 5
- `/sanitization/work/{work_id}/verify-title-changes` (POST) - Lines 419-460
- `/sanitization/extract-toc` (POST) - Lines 963-984
- `/sanitization/extract-titles` (POST) - Lines 987-1006
- `/sanitization/suggest-changes` (POST) - Lines 1009-1033
- `/sanitization/apply-changes` (POST) - Lines 1036-1055

---

### Router: Chunking (`/chunk`)
**File:** `src/psychrag_api/routers/chunking.py`

| Endpoint | Method | Status | UI Usage |
|----------|--------|--------|----------|
| `/chunk/works` | GET | ✅ USED | `chunk/page.tsx:51` |
| `/chunk/work/{work_id}` | GET | ✅ USED | `chunk/[id]/page.tsx:57` |
| `/chunk/work/{work_id}/sanitized/content` | GET | ✅ USED | `chunk/[id]/sanitized/page.tsx:61` |
| `/chunk/work/{work_id}/sanitized/content` | PUT | ✅ USED | `chunk/[id]/sanitized/page.tsx:87` |
| `/chunk/work/{work_id}/extract-sanitized-titles` | POST | ✅ USED | `chunk/[id]/page.tsx:81` |
| `/chunk/work/{work_id}/san-titles/content` | GET | ✅ USED | `chunk/[id]/san-titles/page.tsx:61` |
| `/chunk/work/{work_id}/san-titles/content` | PUT | ✅ USED | `chunk/[id]/san-titles/page.tsx:87` |
| `/chunk/work/{work_id}/vec-suggestions/content` | GET | ❌ UNUSED | None |
| `/chunk/work/{work_id}/vec-suggestions/content` | PUT | ❌ UNUSED | None |
| `/chunk/work/{work_id}/vec-suggestions/table` | GET | ✅ USED | `chunk/[id]/vec-suggestions/page.tsx:93` |
| `/chunk/work/{work_id}/vec-suggestions/table` | PUT | ✅ USED | `chunk/[id]/vec-suggestions/page.tsx:131` |
| `/chunk/work/{work_id}/vec-suggestions/prompt` | GET | ✅ USED | `chunk/[id]/gen-vec-sugg/page.tsx:63` |
| `/chunk/work/{work_id}/vec-suggestions/manual` | POST | ✅ USED | `chunk/[id]/gen-vec-sugg/page.tsx:109` |
| `/chunk/work/{work_id}/vec-suggestions/run` | POST | ✅ USED | `chunk/[id]/gen-vec-sugg/page.tsx:147` |
| `/chunk/work/{work_id}/apply-heading-chunks` | POST | ✅ USED | `chunk/[id]/page.tsx:113` |
| `/chunk/work/{work_id}/apply-content-chunks` | POST | ✅ USED | `chunk/[id]/page.tsx:144` |
| `/chunk/work/{work_id}/chunks/count` | GET | ❌ UNUSED | None |

**UNUSED Endpoints:** 3
- `/chunk/work/{work_id}/vec-suggestions/content` (GET) - Lines 435-474
- `/chunk/work/{work_id}/vec-suggestions/content` (PUT) - Lines 477-545
- `/chunk/work/{work_id}/chunks/count` (GET) - Lines 624-645

**Note:** The `/content` endpoints are superseded by the `/table` endpoints for vec-suggestions.

---

### Router: Vectorization (`/vec`)
**File:** `src/psychrag_api/routers/vectorization.py`

| Endpoint | Method | Status | UI Usage |
|----------|--------|--------|----------|
| `/vec/eligible` | GET | ✅ USED | `vec/page.tsx:34` |
| `/vec/vectorize` | POST | ✅ USED | `vec/page.tsx:61` |

**Summary:** All endpoints USED. No removals needed.

---

### Router: Corpus (`/corpus`)
**File:** `src/psychrag_api/routers/corpus.py`

| Endpoint | Method | Status | UI Usage |
|----------|--------|--------|----------|
| `/corpus/stats` | GET | ✅ USED | `corpus/page.tsx:61` |
| `/corpus/works` | GET | ✅ USED | `corpus/page.tsx:62` |
| `/corpus/work/{work_id}/content` | GET | ✅ USED | `corpus/[id]/page.tsx:42` |

**Summary:** All endpoints USED. No removals needed.

---

### Router: RAG (`/rag`)
**File:** `src/psychrag_api/routers/rag.py`

| Endpoint | Method | Status | UI Usage |
|----------|--------|--------|----------|
| `/rag/queries` | GET | ✅ USED | `rag/page.tsx:77` |
| `/rag/queries/{queryId}` | GET | ✅ USED | `rag/[id]/page.tsx:93` |
| `/rag/queries/{queryId}` | PUT | ✅ USED | `rag/[id]/inspect/page.tsx:106` |
| `/rag/queries/{queryId}/embed` | POST | ✅ USED | `rag/page.tsx:111` |
| `/rag/queries/{queryId}/retrieve` | POST | ✅ USED | `rag/page.tsx:135` |
| `/rag/queries/{queryId}/consolidate` | POST | ✅ USED | `rag/page.tsx:160` |
| `/rag/queries/{queryId}/results` | GET | ✅ USED | `rag/[id]/page.tsx:116` |
| `/rag/queries/{queryId}/results/{resultId}` | GET | ✅ USED | `rag/[id]/results/[resultId]/page.tsx:58` |
| `/rag/expansion/prompt` | POST | ✅ USED | `rag/new/page.tsx:65` |
| `/rag/expansion/manual` | POST | ✅ USED | `rag/new/page.tsx:111` |
| `/rag/expansion/run` | POST | ✅ USED | `rag/new/page.tsx:146` |

**Summary:** All endpoints USED. No removals needed.

---

### Router: RAG Config (`/api/rag-config`)
**File:** `src/psychrag_api/routers/rag_config.py`

| Endpoint | Method | Status | UI Usage |
|----------|--------|--------|----------|
| `/api/rag-config/` | GET | ✅ USED | `components/settings/rag-config-tab.tsx:75` |
| `/api/rag-config/` | POST | ✅ USED | `components/settings/rag-config-tab.tsx:130` |
| `/api/rag-config/{config_id}` | PUT | ✅ USED | `components/settings/rag-config-tab.tsx:173` |
| `/api/rag-config/{config_id}/activate` | POST | ✅ USED | `components/settings/rag-config-tab.tsx:212` |
| `/api/rag-config/{config_id}` | DELETE | ✅ USED | `components/settings/rag-config-tab.tsx:239` |

**Summary:** All endpoints USED. No removals needed.

---

## Summary of Findings

### Total Endpoints Analyzed: 81

### Unused Endpoints: 12

#### Conversion Router (4 unused):
1. `GET /conv/formats` - Stub returning static data
2. `POST /conv/epub` - Stub with TODO comment
3. `POST /conv/pdf` - Stub with TODO comment
4. `GET /conv/status/{job_id}` - Stub with TODO comment

#### Sanitization Router (5 unused):
1. `POST /sanitization/work/{work_id}/verify-title-changes` - Full implementation, never integrated
2. `POST /sanitization/extract-toc` - Legacy stub
3. `POST /sanitization/extract-titles` - Legacy stub
4. `POST /sanitization/suggest-changes` - Legacy stub
5. `POST /sanitization/apply-changes` - Legacy stub

#### Chunking Router (3 unused):
1. `GET /chunk/work/{work_id}/vec-suggestions/content` - Superseded by table endpoint
2. `PUT /chunk/work/{work_id}/vec-suggestions/content` - Superseded by table endpoint
3. `GET /chunk/work/{work_id}/chunks/count` - Debug endpoint, never used in UI

---

## Implementation Plan

### Phase 1: Remove Stub Endpoints (Low Risk) ✅

These are all TODO stubs with no actual implementation:

**Ticket 1.1:** Remove conversion stub endpoints
- File: `src/psychrag_api/routers/conversion.py`
- Remove lines 57-178 (4 stub endpoints)
- Remove related schemas from `src/psychrag_api/schemas/conversion.py`:
  - `SupportedFormatsResponse`
  - `ConversionJobResponse`
  - `ConversionStatusResponse`
- Remove tests: `tests/unit/test_conversion_api_endpoints.py` (if testing these stubs)

**Ticket 1.2:** Remove sanitization legacy stub endpoints
- File: `src/psychrag_api/routers/sanitization.py`
- Remove lines 963-1055 (4 legacy stub endpoints)
- Remove related schemas from `src/psychrag_api/schemas/sanitization.py`:
  - `ExtractTOCRequest`
  - `ExtractTOCResponse`
  - `ExtractTitlesRequest` (legacy version)
  - `ExtractTitlesResponse` (legacy version)
  - `SuggestChangesRequest`
  - `SuggestChangesResponse`
  - `ApplyChangesRequest`
  - `ApplyChangesResponse`
- Note: Keep the work-based versions of these schemas

### Phase 2: Remove Unused Full Implementations (Medium Risk) ✅

**Ticket 2.1:** Remove verify-title-changes endpoint
- File: `src/psychrag_api/routers/sanitization.py`
- Remove lines 419-460 (verify endpoint)
- Remove schema from `src/psychrag_api/schemas/sanitization.py`:
  - `VerifyTitleChangesRequest`
  - `VerifyTitleChangesResponse`
- Remove function: `psychrag/sanitization/verify_title_changes_integrity()`
- Remove tests: Any tests specifically for verify_title_changes

**Ticket 2.2:** Remove vec-suggestions/content endpoints
- File: `src/psychrag_api/routers/chunking.py`
- Remove lines 435-545 (GET and PUT content endpoints)
- Remove schemas from `src/psychrag_api/schemas/chunking.py`:
  - `VecSuggestionsContentResponse`
  - `UpdateVecSuggestionsContentRequest`
- Keep: The table-based endpoints which ARE used

**Ticket 2.3:** Remove chunks/count debug endpoint
- File: `src/psychrag_api/routers/chunking.py`
- Remove lines 624-645 (debug count endpoint)
- No schema removal needed (returns plain dict)

### Phase 3: Testing & Verification ✅

**Ticket 3.1:** Run all tests after removals
- Execute: `pytest tests/unit/`
- Verify no broken tests
- Remove any tests that specifically test removed endpoints

**Ticket 3.2:** Manual UI verification
- Start backend: `uvicorn psychrag_api.main:app`
- Start frontend: `cd psychrag_ui && npm run dev`
- Navigate through all workflow pages
- Verify no console errors related to missing endpoints

---

## Files to Modify

### Backend Files
1. `src/psychrag_api/routers/conversion.py` - Remove 4 stub endpoints
2. `src/psychrag_api/routers/sanitization.py` - Remove 5 unused endpoints
3. `src/psychrag_api/routers/chunking.py` - Remove 3 unused endpoints
4. `src/psychrag_api/schemas/conversion.py` - Remove stub schemas
5. `src/psychrag_api/schemas/sanitization.py` - Remove legacy schemas
6. `src/psychrag_api/schemas/chunking.py` - Remove unused schemas

### Business Logic Files
1. `src/psychrag/sanitization/__init__.py` - Remove verify_title_changes export
2. `src/psychrag/sanitization/verify_title_changes.py` - Delete file (if exists)

### Test Files
1. `tests/unit/test_conversion_api_endpoints.py` - Remove stub tests
2. `tests/unit/test_sanitization_api_endpoints.py` - Remove legacy tests
3. `tests/unit/test_chunking_api_endpoints.py` - Remove unused endpoint tests

---

## Risk Assessment

### Low Risk (9 endpoints)
- All stub/TODO endpoints: Safe to remove, no implementation
- Legacy endpoints: Already superseded by new work-based endpoints

### Medium Risk (3 endpoints)
- `verify-title-changes`: Full implementation but never integrated into UI
- `vec-suggestions/content`: Superseded by table-based approach
- `chunks/count`: Debug endpoint, should be safe to remove

### No High Risk Items
- All unused endpoints are either stubs or have clear alternatives in use

---

## Success Criteria

✅ All 12 unused endpoints removed from route handlers
✅ All related schemas removed
✅ All related unit tests removed or updated
✅ No business logic exclusively used by removed endpoints
✅ All existing tests pass
✅ UI functions normally with no console errors
✅ API documentation updated (OpenAPI tags)

---

## Next Steps

1. ✅ Create implementation tickets (T001-T006)
2. ⏳ Execute Phase 1 (remove stubs)
3. ⏳ Execute Phase 2 (remove full implementations)
4. ⏳ Execute Phase 3 (testing & verification)
5. ⏳ Update documentation
6. ✅ Close this PRD
