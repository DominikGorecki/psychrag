# T02: Rename Python API package: psychrag_api → vulcanlab_api

## Context

- **PRD**: [prd-rename-vulcanlab.md](prd-rename-vulcanlab.md)
- **PRD Sections**: Phase 3 (API Package), Requirements 1.2 (API Package), Requirements 9 (API Routes)
- **User Value**: Rebrands the FastAPI backend service to use VulcanLab naming, including package structure and API endpoint paths. This ensures consistency between the core package and the API layer.

## Outcome

The `src/psychrag_api/` directory is renamed to `src/vulcanlab_api/`, all API imports are updated, FastAPI router prefixes use `/vulcanlab/` instead of `/psychrag/`, and all API unit tests pass.

## Scope

### In scope:
- Rename physical directory `src/psychrag_api/` → `src/vulcanlab_api/`
- Update all `__init__.py` files in the renamed package
- Update all internal imports within the API package
- Update all imports from the core `vulcanlab` package (already renamed in T01)
- Update FastAPI router prefixes from `/psychrag/` to `/vulcanlab/` (if present)
- Update API endpoint paths to use `/vulcanlab/` namespace
- Update test files that import from the API package
- Ensure API unit tests pass with new imports

### Out of scope:
- Core package rename (`src/psychrag/`) - completed in T01
- Frontend rename (`psychrag_ui/`) - handled in T03
- Configuration file names - not being renamed per user guidance
- Documentation updates - handled in T04
- Frontend API client URL updates - handled in T03

## Implementation plan

### Backend - API Package Rename

#### Step 1: Verify T01 completion
Before starting, ensure:
1. `src/vulcanlab/` exists (core package renamed)
2. All imports in the codebase use `from vulcanlab.*`
3. Core package tests pass

#### Step 2: Create feature branch
```bash
git checkout -b feature/rename-api-package
```

#### Step 3: Rename the API package directory
1. Rename `src/psychrag_api/` → `src/vulcanlab_api/`
   - This includes all subdirectories:
     - `routers/`
     - `schemas/`
   - And all files:
     - `__init__.py`
     - `__main__.py`
     - `main.py`
     - `config.py`
     - `dependencies.py`

#### Step 4: Update imports within the API package
Update all imports within `src/vulcanlab_api/`:
- Pattern: `from psychrag_api.` → `from vulcanlab_api.`
- Pattern: `import psychrag_api` → `import vulcanlab_api`

**Key files to update:**
- `src/vulcanlab_api/__init__.py`
- `src/vulcanlab_api/__main__.py`
- `src/vulcanlab_api/main.py` - Main FastAPI app definition
- `src/vulcanlab_api/dependencies.py`
- `src/vulcanlab_api/config.py`
- All files in `src/vulcanlab_api/routers/`
- All files in `src/vulcanlab_api/schemas/`

#### Step 5: Update FastAPI router configurations
Check and update all router definitions in `src/vulcanlab_api/routers/`:

**If routers have prefixes like `/api/psychrag` or `/psychrag`, update them:**
```python
# Before
router = APIRouter(prefix="/api/psychrag")
# After
router = APIRouter(prefix="/api/vulcanlab")
```

**Check these router files:**
- `src/vulcanlab_api/routers/__init__.py`
- `src/vulcanlab_api/routers/rag_config.py`
- `src/vulcanlab_api/routers/templates.py`
- `src/vulcanlab_api/routers/corpus.py`
- `src/vulcanlab_api/routers/vectorization.py`
- `src/vulcanlab_api/routers/settings.py`
- `src/vulcanlab_api/routers/init.py`
- `src/vulcanlab_api/routers/conversion.py` (if exists)

**Also check the main FastAPI app in `main.py`:**
```python
# Check if routers are included with prefixes
app.include_router(some_router, prefix="/psychrag")  # Update to /vulcanlab
```

#### Step 6: Update test imports
Update all test files that import from the API package:
- Pattern: `from psychrag_api.` → `from vulcanlab_api.`
- Pattern: `import psychrag_api` → `import vulcanlab_api`

**Test files to update:**
- `tests/unit/test_api_endpoints.py`
- `tests/unit/test_templates_api.py`
- `tests/unit/test_rag_config_api.py`
- `tests/unit/test_rag_config_integration.py`
- `tests/unit/test_conversion_api_endpoints.py`
- Any other API test files

#### Step 7: Update API test client instantiation
In test files, update any references to the API module:
```python
# Before
from psychrag_api.main import app
# After
from vulcanlab_api.main import app
```

#### Step 8: Update module execution commands
Update any references to running the API module:
```python
# Before: python -m psychrag_api
# After: python -m vulcanlab_api
```

Check for subprocess calls or documentation snippets in code.

#### Step 9: Update string literals
Search for hardcoded strings:
- `"psychrag_api"` → `"vulcanlab_api"`
- `'/psychrag'` → `'/vulcanlab'` (in route definitions)

#### Step 10: Verification checks
```bash
# Check for remaining psychrag_api imports
grep -r "from psychrag_api" src/ --include="*.py"
grep -r "import psychrag_api" src/ --include="*.py"
grep -r "from psychrag_api" tests/ --include="*.py"

# Check for old API paths in route definitions
grep -r '"/psychrag' src/vulcanlab_api/ --include="*.py"
grep -r "'/psychrag" src/vulcanlab_api/ --include="*.py"
```

### Unit tests

Implement the following unit tests:

#### Test 1: API package import verification (`tests/unit/test_api_package_rename.py`)
```python
def test_vulcanlab_api_package_imports():
    """Verify API package can be imported."""
    import vulcanlab_api
    assert vulcanlab_api is not None

def test_vulcanlab_api_main_imports():
    """Verify main FastAPI app can be imported."""
    from vulcanlab_api.main import app
    assert app is not None
    assert app.title is not None

def test_psychrag_api_package_does_not_exist():
    """Verify old psychrag_api package cannot be imported."""
    import importlib
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module('psychrag_api')
```

#### Test 2: Router imports work (`tests/unit/test_api_routers_post_rename.py`)
```python
def test_api_routers_import():
    """Verify all API routers can be imported."""
    from vulcanlab_api.routers import rag_config
    from vulcanlab_api.routers import templates
    from vulcanlab_api.routers import corpus
    from vulcanlab_api.routers import vectorization
    assert all([rag_config, templates, corpus, vectorization])

def test_api_schemas_import():
    """Verify API schemas can be imported."""
    from vulcanlab_api.schemas import common
    from vulcanlab_api.schemas import rag
    assert all([common, rag])
```

#### Test 3: API endpoint paths use new namespace (`tests/unit/test_api_paths.py`)
```python
def test_api_routes_use_vulcanlab_prefix():
    """Verify API routes use /vulcanlab/ prefix instead of /psychrag/."""
    from vulcanlab_api.main import app

    routes = [route.path for route in app.routes]

    # Check no routes contain /psychrag
    psychrag_routes = [r for r in routes if '/psychrag' in r]
    assert len(psychrag_routes) == 0, f"Found routes with /psychrag: {psychrag_routes}"

    # If your API uses prefixes, verify /vulcanlab is present
    # (Adjust this test based on your actual route structure)
    vulcanlab_routes = [r for r in routes if '/vulcanlab' in r]
    # This assertion depends on whether you actually use /vulcanlab in paths
    # Remove if your API doesn't use this prefix
```

#### Test 4: Existing API tests pass
Run the existing API test suite:
```bash
pytest tests/unit/test_api_endpoints.py -v
pytest tests/unit/test_templates_api.py -v
pytest tests/unit/test_rag_config_api.py -v
pytest tests/unit/test_conversion_api_endpoints.py -v
```

**Expected outcome**: All existing API tests should pass with updated imports.

## Dependencies and sequencing

### Dependencies:
- **Prerequisite**: T01 (Core package rename) MUST be completed first
- **Blocks**: None directly, but T03 (UI rename) will need to update API URLs to match
- **Can be done in parallel with**: T03 (Frontend rename)

### Sequencing notes:
- Do NOT start this ticket until T01 is merged and tests pass
- The frontend (T03) can be worked on in parallel after this ticket starts
- Consider doing this work in a feature branch and merging after tests pass
- After merging, the frontend will need to update its API base URLs (handled in T03)

### API Breaking Changes:
**If API endpoints change from `/psychrag/...` to `/vulcanlab/...`:**
- This is a breaking change for any API clients
- The frontend (T03) will need corresponding updates
- External API consumers (if any) will need to be notified

## Clarifications and assumptions

### Assumptions:
1. **API paths should be renamed**: Per user guidance, we're renaming API routes from `/psychrag/` to `/vulcanlab/` (Option A)
2. **No backward compatibility**: No need to support both old and new paths
3. **FastAPI app name can stay generic**: The `app` variable name doesn't need to change, just the routes
4. **Tests use TestClient**: Existing tests use FastAPI TestClient and will continue to work

### Questions (NOT blocking):
- Are there external API clients that need notification of the endpoint changes?
- Is there an API version scheme that should be updated?
- Should OpenAPI/Swagger docs title be updated? (Will be visible in `/docs` endpoint)

### Pre-implementation checklist:
> **Before implementing, review the following:**
> 1. Confirm T01 (core package rename) is complete and merged
> 2. Confirm `src/vulcanlab/` exists and imports work
> 3. Understand current API route structure (check if `/psychrag` prefix is actually used)
> 4. Review how frontend calls the API to understand breaking changes

## Manual test plan

After implementation, manually verify:

### Test 1: API package import
```bash
# Activate venv
venv\Scripts\activate

# Import the API package
python -c "from vulcanlab_api.main import app; print('Success')"
python -c "from vulcanlab_api.dependencies import get_db; print('Success')"
```

### Test 2: Start the API server
```bash
# Run the API server
python -m vulcanlab_api

# Or using uvicorn directly
uvicorn vulcanlab_api.main:app --reload
```

**Expected**: Server starts without import errors

### Test 3: Check API documentation
```bash
# Start server, then visit in browser:
http://localhost:8000/docs
```

**Expected**:
- Swagger UI loads
- No endpoints show `/psychrag/` in paths
- All endpoints use `/vulcanlab/` (or no prefix, depending on your structure)

### Test 4: Run API tests
```bash
pytest tests/unit/test_api_endpoints.py -v
pytest tests/unit/test_templates_api.py -v
pytest tests/unit/test_rag_config_api.py -v
```

### Test 5: Check for missed references
```bash
# Should return no results
grep -r "from psychrag_api" src/ --include="*.py"
grep -r "import psychrag_api" src/ --include="*.py"
grep -r '"/psychrag' src/vulcanlab_api/ --include="*.py"
```

### Test 6: Test an API endpoint manually
```bash
# Using curl or similar (adjust endpoint to your actual API)
curl http://localhost:8000/vulcanlab/api/health
# Or whatever health check endpoint exists
```

## Success criteria

- [ ] Directory `src/psychrag_api/` renamed to `src/vulcanlab_api/`
- [ ] All imports within API package updated
- [ ] All test imports updated
- [ ] FastAPI router prefixes updated (if applicable)
- [ ] API routes use `/vulcanlab/` instead of `/psychrag/`
- [ ] All new unit tests pass
- [ ] All existing API unit tests pass
- [ ] API server starts: `python -m vulcanlab_api`
- [ ] No grep results for `psychrag_api` in `src/` and `tests/`
- [ ] Swagger/OpenAPI docs load at `/docs`
- [ ] API endpoints are accessible and return expected responses
