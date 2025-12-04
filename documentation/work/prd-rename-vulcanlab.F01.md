# T01: Rename Python core package: psychrag → vulcanlab

## Context

- **PRD**: [prd-rename-vulcanlab.md](prd-rename-vulcanlab.md)
- **PRD Sections**: Phase 2 (Core Python Package), Requirements 1 (Python Package Renaming)
- **User Value**: Complete rebranding of the core Python package from PsychRAG to VulcanLab, establishing the foundation for the entire rename effort. This is the critical first step that all other tickets depend on.

## Outcome

The `src/psychrag/` directory is renamed to `src/vulcanlab/`, all Python imports throughout the codebase reference `vulcanlab` instead of `psychrag`, all CLI module commands use the new `vulcanlab` namespace, and all unit tests pass with the new package structure.

## Scope

### In scope:
- Rename physical directory `src/psychrag/` → `src/vulcanlab/`
- Update all `__init__.py` files in the renamed package
- Update all internal imports within the core package
- Update all imports from external files (API, tests, migrations) that reference the core package
- Update all `python -m` module references in code and CLI scripts
- Update test files that import from the core package
- Ensure unit tests pass with new imports
- Update any hardcoded string references to "psychrag" module names in the core package

### Out of scope:
- API package rename (`src/psychrag_api/`) - handled in T02
- Frontend rename (`psychrag_ui/`) - handled in T03
- Configuration file names (`psychrag.config.json`) - not being renamed per user guidance
- Database names or migrations - not needed per user guidance
- Documentation files - handled in T04
- User-facing text updates - handled in T04

## Implementation plan

### Backend - Core Package Rename

#### Step 1: Backup and preparation
1. Ensure git working tree is clean
2. Create a feature branch for this work: `git checkout -b feature/rename-core-package`

#### Step 2: Rename the core package directory
1. Rename `src/psychrag/` → `src/vulcanlab/`
   - This includes all subdirectories:
     - `ai/`
     - `augmentation/`
     - `chunking/`
     - `config/`
     - `conversions/`
     - `data/`
     - `retrieval/`
     - `sanitization/`
     - `utils/`
     - `vectorization/`

#### Step 3: Update all imports within the core package
Find and replace all internal imports:
- Pattern: `from psychrag.` → `from vulcanlab.`
- Pattern: `import psychrag.` → `import vulcanlab.`
- Files to update: All `.py` files in `src/vulcanlab/`

**Key files that likely contain many imports:**
- `src/vulcanlab/__init__.py`
- `src/vulcanlab/config/app_config.py`
- `src/vulcanlab/data/database.py`
- `src/vulcanlab/data/init_db.py`
- All CLI files (`*_cli.py`)
- All model files in `src/vulcanlab/data/models/`

#### Step 4: Update imports in API package
Update all files in `src/psychrag_api/` that import from the core package:
- Pattern: `from psychrag.` → `from vulcanlab.`
- Pattern: `import psychrag` → `import vulcanlab`

**Files to check:**
- `src/psychrag_api/dependencies.py`
- `src/psychrag_api/config.py`
- `src/psychrag_api/main.py`
- All files in `src/psychrag_api/routers/`
- All files in `src/psychrag_api/schemas/`

#### Step 5: Update test imports
Update all test files:
- Pattern: `from psychrag.` → `from vulcanlab.`
- Pattern: `import psychrag` → `import vulcanlab`

**Files to update:**
- `tests/unit/test_*.py` (all test files)
- Any test fixtures or conftest files

#### Step 6: Update migration scripts
Check and update any migration scripts in `migrations/`:
- Pattern: `from psychrag.` → `from vulcanlab.`

#### Step 7: Update module execution references
Search for any `python -m psychrag.*` references in:
- Python files with subprocess calls
- Shell scripts
- Any automation scripts

Replace with `python -m vulcanlab.*`

#### Step 8: Update string literals
Search for hardcoded strings that reference the module name:
- `"psychrag."` → `"vulcanlab."`
- `'psychrag.'` → `'vulcanlab.'`

**Common locations:**
- Logging statements
- Error messages
- Configuration loaders
- Module introspection code

#### Step 9: Verification checks
Run the following commands to verify completeness:
```bash
# Check for remaining psychrag imports (should return no .py files in src/)
grep -r "from psychrag\." src/ --include="*.py"
grep -r "import psychrag" src/ --include="*.py"

# Check for module references
grep -r "python -m psychrag" . --include="*.py"

# Check for string literals in core package
grep -r '"psychrag' src/vulcanlab/ --include="*.py"
grep -r "'psychrag" src/vulcanlab/ --include="*.py"
```

### Unit tests

Implement the following unit tests to verify the rename:

#### Test 1: Import verification (`tests/unit/test_package_rename.py`)
```python
def test_vulcanlab_package_imports():
    """Verify core vulcanlab package can be imported."""
    import vulcanlab
    assert vulcanlab is not None

def test_vulcanlab_submodules_import():
    """Verify all major submodules can be imported."""
    from vulcanlab import config
    from vulcanlab import data
    from vulcanlab import ai
    from vulcanlab import augmentation
    from vulcanlab import chunking
    from vulcanlab import conversions
    from vulcanlab import retrieval
    from vulcanlab import sanitization
    from vulcanlab import utils
    from vulcanlab import vectorization
    assert all([config, data, ai, augmentation, chunking,
                conversions, retrieval, sanitization, utils, vectorization])

def test_psychrag_package_does_not_exist():
    """Verify old psychrag package cannot be imported."""
    import importlib
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module('psychrag')
```

#### Test 2: Key module functionality (`tests/unit/test_core_modules_post_rename.py`)
```python
def test_app_config_loads_with_new_import():
    """Verify AppConfig works with new import path."""
    from vulcanlab.config import AppConfig
    # Test basic instantiation works
    config = AppConfig.from_json_file("psychrag.config.json")
    assert config is not None

def test_database_module_imports():
    """Verify database module works with new imports."""
    from vulcanlab.data.database import get_engine, get_session
    assert callable(get_engine)
    assert callable(get_session)

def test_cli_modules_importable():
    """Verify CLI modules can be imported (even if not executed)."""
    from vulcanlab.config import app_config_cli
    from vulcanlab.data import init_db
    assert app_config_cli is not None
    assert init_db is not None
```

#### Test 3: Existing unit tests pass
Run the existing test suite to ensure no regressions:
```bash
pytest tests/unit/ -v
```

**Expected outcome**: All existing tests should pass with updated imports.

**Key test files to verify:**
- `tests/unit/test_augment.py`
- `tests/unit/test_api_endpoints.py`
- `tests/unit/test_database.py`
- `tests/unit/test_init_db.py`
- `tests/unit/test_conv_pdf2md.py`
- `tests/unit/test_conv_epub2md.py`
- `tests/unit/test_inspection.py`
- All RAG config tests

## Dependencies and sequencing

### Dependencies:
- **Prerequisite**: None - this is the first ticket
- **Blocks**: T02 (API rename), T03 (UI rename), T04 (Documentation)

### Sequencing notes:
- This ticket MUST be completed before any other rename tickets
- The API package (T02) depends on this being done first
- Consider doing this work in a feature branch and merging only after all tests pass
- Do NOT update `pyproject.toml` (it already has `name = "VulcanLab"`)

### Rollback strategy:
If issues arise:
1. Use git to revert the branch
2. The rename is atomic - either all imports work or none do
3. Tests will catch any missed imports

## Clarifications and assumptions

### Assumptions:
1. **Config file stays as-is**: We are NOT renaming `psychrag.config.json` to `vulcanlab.config.json` per user guidance
2. **No database migration**: We are NOT renaming database names (`psych_rag_test`) per user guidance
3. **Breaking change is acceptable**: This is a hard cutover with no backward compatibility
4. **pyproject.toml is already correct**: The `name = "VulcanLab"` is already set, no change needed
5. **Module structure stays the same**: We're only renaming, not reorganizing the package structure

### Questions (NOT blocking, but good to confirm):
- Are there any internal tools or scripts outside the repo that import `psychrag`?
- Do any CI/CD pipelines have hardcoded `python -m psychrag.*` commands?

### Pre-implementation checklist:
> **Before implementing, review the following:**
> 1. Confirm that NO existing user config files need updating (per user guidance)
> 2. Confirm git branch is clean and up to date
> 3. Ensure virtual environment can be recreated after the rename
> 4. Have a backup or be prepared to use git to rollback if needed

## Manual test plan

After implementation, manually verify:

### Test 1: Basic import check
```bash
# Activate venv
venv\Scripts\activate

# Try importing the new package
python -c "import vulcanlab; print('Success')"
python -c "from vulcanlab.config import AppConfig; print('Success')"
```

### Test 2: CLI module execution
```bash
# Test key CLI commands work
python -m vulcanlab.config.app_config_cli show
python -m vulcanlab.data.db_health_check_cli
```

### Test 3: Run test suite
```bash
pytest tests/unit/ -v
```

### Test 4: Check for missed references
```bash
# Should return no results in src/
grep -r "from psychrag\." src/ --include="*.py"
grep -r "import psychrag" src/ --include="*.py"
```

### Test 5: Verify package structure
```bash
# List the new package structure
ls -la src/vulcanlab/
# Should show all subdirectories: ai, augmentation, chunking, config, etc.
```

## Success criteria

- [ ] Directory `src/psychrag/` renamed to `src/vulcanlab/`
- [ ] All imports in core package updated
- [ ] All imports in API package updated
- [ ] All imports in test files updated
- [ ] All new unit tests pass
- [ ] All existing unit tests pass
- [ ] No grep results for `from psychrag.` in `src/` directory
- [ ] CLI commands work: `python -m vulcanlab.config.app_config_cli show`
- [ ] Package can be installed: `pip install -e .` succeeds
