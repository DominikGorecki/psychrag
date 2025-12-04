# T006: Final verification and documentation update

## Context

- **PRD**: [cleanup-unused-api-calls.md](cleanup-unused-api-calls.md)
- **PRD Section**: Phase 3: Testing & Verification
- **User value**: Ensures all API endpoint removals (T001-T005) were successful and haven't broken any functionality. Updates documentation to reflect the cleaned-up API surface.

## Outcome

All unused endpoints have been successfully removed with full verification that:
- The test suite passes completely
- The UI functions normally
- API documentation is accurate
- No regressions were introduced

## Scope

### In scope
- Run complete test suite across all modules
- Perform comprehensive UI workflow testing
- Verify OpenAPI documentation is accurate
- Check for any orphaned imports, schemas, or tests
- Update any documentation that references removed endpoints
- Create summary of changes for release notes

### Out of scope
- Additional endpoint removals (all handled in T001-T005)
- Feature development or improvements
- Performance optimization

## Implementation plan

### Prerequisites verification

#### Step 1: Confirm all removal tickets are complete
Before starting verification, ensure T001-T005 have all been implemented:

```bash
# Check git log or review PR/commits to confirm:
# - T001: 4 conversion stub endpoints removed
# - T002: 4 sanitization legacy endpoints removed
# - T003: 1 verify-title-changes endpoint removed
# - T004: 2 vec-suggestions content endpoints removed
# - T005: 1 chunks/count debug endpoint removed
```

If any ticket is incomplete, complete it before proceeding.

### Comprehensive testing

#### Step 2: Run full test suite
Execute the entire test suite to catch any issues:

```bash
cd c:\code\python\psychRAG-test
venv\Scripts\activate

# Run all unit tests with verbose output
pytest tests/unit/ -v --tb=short

# If integration tests exist, run those too
pytest tests/integration/ -v --tb=short

# Generate coverage report to see what's tested
pytest tests/ --cov=src/psychrag --cov=src/psychrag_api --cov-report=html
```

**Success criteria**:
- All tests pass (0 failures)
- No import errors
- No missing module/function errors
- Coverage report shows no drop in coverage

If any tests fail:
1. Investigate the failure
2. Determine if it's related to the removals
3. Fix the issue (may need to remove missed test or fix incorrect dependency)
4. Re-run tests until all pass

#### Step 3: Check for orphaned code
Search for references to removed endpoints that may have been missed:

```bash
# Search for removed endpoint paths
grep -r "/conv/formats\|/conv/epub\|/conv/pdf\|/conv/status" src/
grep -r "/sanitization/extract-toc\|/sanitization/extract-titles" src/
grep -r "/sanitization/suggest-changes\|/sanitization/apply-changes" src/
grep -r "verify-title-changes" src/
grep -r "vec-suggestions/content" src/
grep -r "chunks/count" src/

# Search for removed function names
grep -r "get_supported_formats\|convert_epub\|convert_pdf\|get_conversion_status" src/
grep -r "verify_title_changes_integrity" src/
grep -r "get_vec_suggestions_content\|update_vec_suggestions_content" src/
grep -r "get_chunk_count" src/
```

**Expected result**: No matches found (except in comments or docstrings explaining the removal)

If matches are found:
- Review each occurrence
- Determine if it should be removed or updated
- Make necessary changes

### UI verification

#### Step 4: Start backend and verify API docs
```bash
cd c:\code\python\psychRAG-test
venv\Scripts\activate
uvicorn psychrag_api.main:app --reload
```

Visit http://localhost:8000/docs and manually verify:

**Conversion section** - should NOT contain:
- ❌ GET /conv/formats
- ❌ POST /conv/epub
- ❌ POST /conv/pdf
- ❌ GET /conv/status/{job_id}

**Sanitization section** - should NOT contain:
- ❌ POST /sanitization/extract-toc
- ❌ POST /sanitization/extract-titles (legacy)
- ❌ POST /sanitization/suggest-changes
- ❌ POST /sanitization/apply-changes
- ❌ POST /sanitization/work/{work_id}/verify-title-changes

**Chunking section** - should NOT contain:
- ❌ GET /chunk/work/{work_id}/vec-suggestions/content
- ❌ PUT /chunk/work/{work_id}/vec-suggestions/content
- ❌ GET /chunk/work/{work_id}/chunks/count

All other endpoints should be present and documented.

#### Step 5: Comprehensive UI workflow testing
Start the UI and test all major workflows:

```bash
cd psychrag_ui
npm run dev
```

Open http://localhost:3000 and test:

**Settings workflow**:
- ✅ Navigate to Settings
- ✅ View/edit database configuration
- ✅ View/edit LLM configuration
- ✅ View/edit paths configuration
- ✅ Manage prompt templates
- ✅ No console errors

**Conversion workflow**:
- ✅ Navigate to Conversion page
- ✅ View list of convertible files
- ✅ Convert a file (EPUB or docx)
- ✅ Inspect converted output
- ✅ Add to database
- ✅ No console errors

**Sanitization workflow**:
- ✅ Navigate to Sanitization page
- ✅ View list of works
- ✅ Select a work
- ✅ Extract titles
- ✅ Generate title changes (AI or manual)
- ✅ Review/edit title changes (table view)
- ✅ Apply title changes
- ✅ No console errors

**Chunking workflow**:
- ✅ Navigate to Chunking page
- ✅ View list of works with sanitized files
- ✅ Select a work
- ✅ Extract sanitized titles
- ✅ Generate vec suggestions (AI or manual)
- ✅ Review/edit vec suggestions (table view)
- ✅ Apply heading chunks
- ✅ Apply content chunks
- ✅ No console errors

**Vectorization workflow**:
- ✅ Navigate to Vectorization page
- ✅ View eligible works
- ✅ Vectorize a work
- ✅ No console errors

**Corpus workflow**:
- ✅ Navigate to Corpus page
- ✅ View corpus statistics
- ✅ View list of corpus works
- ✅ View work content
- ✅ No console errors

**RAG workflow**:
- ✅ Navigate to RAG page
- ✅ Create new query
- ✅ Expand query
- ✅ Embed, retrieve, consolidate
- ✅ View results
- ✅ No console errors

**Browser console check**:
- No 404 errors for removed endpoints
- No JavaScript errors
- No failed API calls

### Documentation updates

#### Step 6: Update project documentation
Check if any documentation files reference the removed endpoints:

```bash
# Search documentation for removed endpoint references
grep -r "conv/formats\|conv/epub\|conv/pdf\|conv/status" docs/ README.md
grep -r "extract-toc\|verify-title-changes" docs/ README.md
grep -r "vec-suggestions/content\|chunks/count" docs/ README.md
```

If found, update the documentation to remove references to these endpoints.

#### Step 7: Create removal summary
Document what was removed for future reference and release notes:

Create or update a file: `docs/CHANGELOG.md` or similar

Add an entry like:
```markdown
## [Version X.X.X] - 2025-MM-DD

### Removed
- **Conversion API**: Removed 4 stub endpoints that were never implemented
  - GET /conv/formats
  - POST /conv/epub
  - POST /conv/pdf
  - GET /conv/status/{job_id}

- **Sanitization API**: Removed 5 unused endpoints
  - 4 legacy endpoints superseded by work-based API
  - 1 verify-title-changes endpoint that was never integrated

- **Chunking API**: Removed 3 unused endpoints
  - 2 vec-suggestions content endpoints (superseded by table endpoints)
  - 1 debug chunks/count endpoint

**Impact**: No user-facing impact. All removed endpoints were unused by the UI.
**Total**: 12 endpoints removed, reducing API surface area and maintenance burden.
```

### Final cleanup

#### Step 8: Check for unused imports
Look for any imports that may have become unused after all the removals:

```bash
# Use a linter or manually check each modified file
cd src/psychrag_api/routers
# Review: conversion.py, sanitization.py, chunking.py

cd ../schemas
# Review: conversion.py, sanitization.py, chunking.py
```

Remove any unused imports to keep the code clean.

#### Step 9: Run linters and formatters
```bash
# If using black for formatting
black src/psychrag_api/

# If using flake8 for linting
flake8 src/psychrag_api/ --max-line-length=120

# If using mypy for type checking
mypy src/psychrag_api/
```

Fix any issues raised by linters.

## Unit tests

### No new tests needed
This ticket is verification-only. The goal is to ensure all existing tests pass after the removals from T001-T005.

### Test verification checklist
- [ ] All unit tests pass: `pytest tests/unit/ -v`
- [ ] All integration tests pass (if they exist)
- [ ] No orphaned test files or functions remain
- [ ] Coverage hasn't decreased significantly

## Manual test plan

This entire ticket IS the manual test plan. Follow Steps 1-9 sequentially, checking off each item as completed.

**Quick verification checklist**:
- [ ] All removal tickets (T001-T005) completed
- [ ] Full test suite passes with 0 failures
- [ ] No orphaned code found in grep searches
- [ ] OpenAPI docs accurate (removed endpoints gone)
- [ ] All UI workflows tested and working
- [ ] No console errors in browser
- [ ] Documentation updated
- [ ] CHANGELOG or release notes created
- [ ] Unused imports removed
- [ ] Linters pass

## Dependencies and sequencing

### Prerequisites
**MUST be completed BEFORE this ticket**:
- T001: Conversion stub endpoints removed
- T002: Sanitization legacy endpoints removed
- T003: Verify-title-changes endpoint removed
- T004: Vec-suggestions content endpoints removed
- T005: Chunks/count debug endpoint removed

### Blocks
- Release/deployment (this ticket must pass before releasing)

### Cannot be done in parallel
This ticket must be done LAST, after all removal tickets are complete.

## Clarifications and assumptions

### Assumptions
1. **All removals complete**: T001-T005 have been fully implemented and committed
2. **Test infrastructure works**: The test suite is functional and comprehensive
3. **UI is runnable**: Both backend and frontend can be started locally
4. **Documentation structure**: Project has standard documentation files (README, CHANGELOG, etc.)

### Non-blocking clarifications
- **Release timing**: When should this cleanup be released?
- **Communication**: Should we announce these removals to any stakeholders?

### Prompt for implementer
> This is the final verification ticket. Do not start this ticket until ALL removal tickets (T001-T005) are complete and committed. This ticket's job is to catch any issues that may have been missed in individual tickets and ensure the entire system still works correctly. Be thorough and methodical - take your time with each verification step.

## Success criteria

- [ ] All 12 endpoints successfully removed (verified in OpenAPI docs)
- [ ] Full test suite passes with 0 failures
- [ ] No orphaned code or references to removed endpoints
- [ ] All UI workflows tested and working normally
- [ ] No console errors or failed API calls in browser
- [ ] Documentation updated to reflect removals
- [ ] CHANGELOG or release notes created
- [ ] Code is clean (no unused imports, linters pass)
- [ ] Ready for release

## Post-verification checklist

Once all success criteria are met:
1. Create a summary of verification results
2. Update the PRD with "COMPLETE" status
3. Notify the team that cleanup is ready for review/merge
4. Prepare for code review (if applicable)
5. Plan release/deployment
