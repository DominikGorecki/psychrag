# T05: Final verification and cleanup

## Context

- **PRD**: [prd-rename-vulcanlab.md](prd-rename-vulcanlab.md)
- **PRD Sections**: Phase 7 (Testing & Verification), Phase 8 (Final Cleanup)
- **User Value**: Ensures the rename is complete, consistent, and functional across the entire codebase. Provides confidence that nothing was missed and the system works end-to-end with the new VulcanLab branding.

## Outcome

All unit tests pass, all integration points work, no broken references remain, the full application stack (backend + frontend) runs successfully, and a comprehensive verification report documents the completion of the rename.

## Scope

### In scope:
- Run complete test suite (all unit tests)
- Verify all package imports work
- Verify CLI commands work
- Verify API server starts and endpoints respond
- Verify frontend builds and runs
- Comprehensive grep searches for missed references
- Create verification checklist/report
- Update project-specific files (workspace config, IDE settings if needed)
- Final cleanup of any remaining references

### Out of scope:
- Writing new features or tests (only running existing ones)
- Database migration (not needed per user guidance)
- Updating external systems or deployment configs (separate task)
- User communication or migration guides (separate task)

## Implementation plan

### Verification and Cleanup

#### Step 1: Verify all prerequisites complete
Before starting, ensure:
1. T01 (core package rename) is merged
2. T02 (API package rename) is merged
3. T03 (frontend package rename) is merged
4. T04 (documentation updates) is merged

#### Step 2: Create verification branch
```bash
git checkout main
git pull
git checkout -b verification/rename-complete
```

#### Step 3: Run full Python test suite
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Unix/Mac

# Run all unit tests
pytest tests/unit/ -v

# Run with coverage to see test coverage
pytest tests/unit/ -v --cov=vulcanlab --cov=vulcanlab_api
```

**Expected outcome**: All tests pass

**If tests fail:**
- Document the failure
- Determine if it's related to the rename
- Fix and re-run tests
- Update T01-T04 tickets if patterns were missed

#### Step 4: Verify package imports
Test that all major modules can be imported:

```python
# Create a test script: verify_imports.py
import sys

def test_imports():
    """Verify all major vulcanlab modules can be imported."""
    errors = []

    try:
        import vulcanlab
        print("✓ vulcanlab")
    except ImportError as e:
        errors.append(f"✗ vulcanlab: {e}")

    try:
        from vulcanlab.config import AppConfig
        print("✓ vulcanlab.config")
    except ImportError as e:
        errors.append(f"✗ vulcanlab.config: {e}")

    try:
        from vulcanlab.data import database
        print("✓ vulcanlab.data")
    except ImportError as e:
        errors.append(f"✗ vulcanlab.data: {e}")

    try:
        from vulcanlab.ai import llm_factory
        print("✓ vulcanlab.ai")
    except ImportError as e:
        errors.append(f"✗ vulcanlab.ai: {e}")

    try:
        from vulcanlab_api.main import app
        print("✓ vulcanlab_api")
    except ImportError as e:
        errors.append(f"✗ vulcanlab_api: {e}")

    if errors:
        print("\nErrors found:")
        for error in errors:
            print(error)
        sys.exit(1)
    else:
        print("\n✓ All imports successful")

if __name__ == "__main__":
    test_imports()
```

Run it:
```bash
python verify_imports.py
```

#### Step 5: Verify CLI commands
Test key CLI commands work:

```bash
# Test config CLI
python -m vulcanlab.config.app_config_cli show

# Test database health check
python -m vulcanlab.data.db_health_check_cli

# Test other key CLIs (pick 2-3 important ones)
python -m vulcanlab.utils.model_info_cli --help
```

**Expected outcome**: Commands run without ImportError or ModuleNotFoundError

**Document any errors** for fixing.

#### Step 6: Verify API server
Start the API and test endpoints:

```bash
# Start API server
python -m vulcanlab_api
# Should start without errors
```

In another terminal or using curl:
```bash
# Test API documentation loads
curl http://localhost:8000/docs
# Should return HTML

# Test a health check endpoint (if exists)
curl http://localhost:8000/health
# Or whichever endpoint exists

# Check API routes
curl http://localhost:8000/openapi.json | grep "psychrag"
# Should return no matches
```

**Expected outcome**:
- Server starts successfully
- No import errors in logs
- API docs accessible at `/docs`
- No `/psychrag/` routes in OpenAPI spec

#### Step 7: Verify frontend build and run
Test the UI builds and runs:

```bash
cd vulcanlab_ui

# Clean install
rm -rf node_modules .next
npm install

# Build production version
npm run build
# Should succeed

# Start dev server
npm run dev
# Should start on http://localhost:3000
```

**Manual browser test:**
1. Open http://localhost:3000
2. Check browser console for errors
3. Check Network tab for API calls
4. Verify API calls go to `/vulcanlab/` endpoints
5. Verify page title shows "VulcanLab"

#### Step 8: Comprehensive search for missed references
Run systematic searches for remaining "psychrag" references:

```bash
# Create a comprehensive search script: verify_no_psychrag.sh

#!/bin/bash
echo "=== Comprehensive PsychRAG reference check ==="
echo ""

FOUND=0

echo "1. Checking Python source files..."
if grep -r "from psychrag\." src/ --include="*.py" 2>/dev/null; then
    echo "   ✗ Found 'from psychrag.' imports"
    FOUND=1
else
    echo "   ✓ No 'from psychrag.' imports"
fi

if grep -r "import psychrag" src/ --include="*.py" 2>/dev/null; then
    echo "   ✗ Found 'import psychrag' statements"
    FOUND=1
else
    echo "   ✓ No 'import psychrag' statements"
fi

echo ""
echo "2. Checking test files..."
if grep -r "from psychrag" tests/ --include="*.py" 2>/dev/null; then
    echo "   ✗ Found psychrag imports in tests"
    FOUND=1
else
    echo "   ✓ No psychrag imports in tests"
fi

echo ""
echo "3. Checking for psychrag_api references..."
if grep -r "psychrag_api" src/ --include="*.py" 2>/dev/null; then
    echo "   ✗ Found psychrag_api references"
    FOUND=1
else
    echo "   ✓ No psychrag_api references"
fi

echo ""
echo "4. Checking frontend source..."
if grep -r "psychrag" vulcanlab_ui/src/ --include="*.ts" --include="*.tsx" --include="*.js" 2>/dev/null; then
    echo "   ✗ Found psychrag in UI source"
    FOUND=1
else
    echo "   ✓ No psychrag in UI source"
fi

echo ""
echo "5. Checking for old API paths in frontend..."
if grep -r '"/psychrag' vulcanlab_ui/src/ --include="*.ts" --include="*.tsx" 2>/dev/null; then
    echo "   ✗ Found /psychrag paths in UI"
    FOUND=1
else
    echo "   ✓ No /psychrag paths in UI"
fi

echo ""
echo "6. Checking documentation..."
if grep -ri "python -m psychrag\." documentation/ --include="*.md" 2>/dev/null | grep -v "rename-to-vulcanlab"; then
    echo "   ✗ Found old commands in docs"
    FOUND=1
else
    echo "   ✓ Docs use new commands"
fi

echo ""
echo "7. Checking README..."
if grep -i "psychrag" README.md 2>/dev/null | grep -v "psychrag.config.json"; then
    echo "   ✗ Found psychrag in README (excluding config filename)"
    FOUND=1
else
    echo "   ✓ README clean"
fi

echo ""
if [ $FOUND -eq 0 ]; then
    echo "=== ✓ All checks passed ==="
    exit 0
else
    echo "=== ✗ Some checks failed - review above ==="
    exit 1
fi
```

Run the script:
```bash
bash verify_no_psychrag.sh
```

**Expected outcome**: All checks pass

**Allowed exceptions:**
- `psychrag.config.json` - config filename (not renamed)
- `documentation/work/rename-to-vulcanlab.*` - historical rename docs
- Git history - not modifying past commits

#### Step 9: Update workspace and IDE files (if needed)
Check for workspace-specific files:

```bash
# Check for workspace files
ls *.code-workspace 2>/dev/null

# Check for IDE config directories
ls -la | grep -E "\.vscode|\.idea"
```

**If found:**
- Update `.code-workspace` files to reference `vulcanlab_ui/` instead of `psychrag_ui/`
- Update any IDE run configurations that reference old module names
- Update any IDE path mappings

**Example** (`.vscode/settings.json` if it exists):
```json
{
  "python.autoComplete.extraPaths": [
    "${workspaceFolder}/src"
  ],
  // Verify no psychrag references
}
```

#### Step 10: Create verification report
Create a final verification document:

**File:** `documentation/work/verification-report-rename.md`

```markdown
# VulcanLab Rename Verification Report

**Date:** [Current date]
**Tickets Completed:** T01, T02, T03, T04, T05

## Verification Results

### Test Suite
- [ ] All unit tests pass: `pytest tests/unit/ -v`
- [ ] Test count: [X] tests passed

### Import Verification
- [ ] Core package imports work
- [ ] API package imports work
- [ ] All submodules accessible

### CLI Commands
- [ ] `python -m vulcanlab.config.app_config_cli show` - Works
- [ ] `python -m vulcanlab.data.db_health_check_cli` - Works
- [ ] [Other key commands] - Works

### API Server
- [ ] Server starts: `python -m vulcanlab_api`
- [ ] API docs accessible: http://localhost:8000/docs
- [ ] No psychrag routes in OpenAPI spec

### Frontend
- [ ] Build succeeds: `npm run build`
- [ ] Dev server starts: `npm run dev`
- [ ] App loads in browser
- [ ] Browser console clean (no errors)
- [ ] API calls use /vulcanlab/ paths

### Reference Check
- [ ] No `from psychrag.` in src/
- [ ] No `import psychrag` in src/
- [ ] No psychrag references in tests/
- [ ] No psychrag in UI source
- [ ] Documentation updated
- [ ] README updated

### Documentation
- [ ] README.md shows VulcanLab
- [ ] MkDocs builds successfully
- [ ] User-facing text updated

## Remaining Items
- Config filename: `psychrag.config.json` - Kept as-is (per requirements)
- Historical docs: References preserved where appropriate

## Sign-off
The VulcanLab rename is complete and verified.
```

#### Step 11: Final cleanup
1. Remove any temporary verification scripts if not needed
2. Ensure `.gitignore` doesn't need updates
3. Check if there are any old `__pycache__` directories with old names

```bash
# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Reinstall package to ensure clean state
pip install -e .
```

### Unit tests

This ticket primarily runs existing tests rather than creating new ones. However, create one final integration test:

#### Test: End-to-end smoke test (`tests/integration/test_rename_complete.py`)
```python
"""Integration test to verify rename is complete."""
import subprocess
import sys

def test_core_package_imports():
    """Verify core package can be imported."""
    import vulcanlab
    from vulcanlab.config import AppConfig
    from vulcanlab.data import database
    assert vulcanlab is not None

def test_api_package_imports():
    """Verify API package can be imported."""
    import vulcanlab_api
    from vulcanlab_api.main import app
    assert vulcanlab_api is not None
    assert app is not None

def test_no_psychrag_imports():
    """Verify psychrag package doesn't exist."""
    import importlib
    try:
        importlib.import_module('psychrag')
        assert False, "psychrag package should not exist"
    except ModuleNotFoundError:
        pass  # Expected

    try:
        importlib.import_module('psychrag_api')
        assert False, "psychrag_api package should not exist"
    except ModuleNotFoundError:
        pass  # Expected

def test_cli_commands_exist():
    """Verify key CLI commands can be invoked."""
    # Test help flag (shouldn't execute, just verify command exists)
    result = subprocess.run(
        [sys.executable, "-m", "vulcanlab.config.app_config_cli", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "CLI command should work"
    assert "vulcanlab" in result.stdout.lower() or "usage" in result.stdout.lower()

def test_package_name_in_pyproject():
    """Verify pyproject.toml has correct name."""
    import tomllib  # Python 3.11+, or use tomli for earlier versions
    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)
    assert config["project"]["name"] == "VulcanLab"
```

Run this test:
```bash
pytest tests/integration/test_rename_complete.py -v
```

## Dependencies and sequencing

### Dependencies:
- **Prerequisite**: T01 (core package rename) merged
- **Prerequisite**: T02 (API package rename) merged
- **Prerequisite**: T03 (frontend package rename) merged
- **Prerequisite**: T04 (documentation updates) merged
- **Blocks**: None - this is the final ticket

### Sequencing notes:
- This must be the LAST ticket
- All other tickets must be merged before starting this
- This ticket validates the entire rename effort
- Consider doing this on a fresh clone to avoid cached issues

## Clarifications and assumptions

### Assumptions:
1. **All previous tickets complete**: T01-T04 are merged to main/master
2. **Clean environment**: Tests run in a properly set up environment
3. **pytest is available**: Test framework is installed
4. **Node.js available**: For frontend testing
5. **No external dependencies**: System under test doesn't require external services (or they're mocked)

### Questions (NOT blocking):
- Should we create a tagged release after this verification?
- Are there deployment environments that need updating?
- Should we notify any external stakeholders?

### Pre-implementation checklist:
> **Before implementing, review the following:**
> 1. Confirm all T01-T04 tickets are merged
> 2. Consider doing verification on a fresh git clone to catch path issues
> 3. Ensure test environment is clean (fresh venv, fresh npm install)
> 4. Have a checklist of all expected verification steps

## Manual test plan

This entire ticket IS a manual test plan. Key steps:

### Test 1: Fresh environment setup
```bash
# Clone repo fresh or pull latest
git clone <repo> vulcanlab-verify
cd vulcanlab-verify

# Set up Python environment
python -m venv venv
venv\Scripts\activate
pip install -e .

# Set up frontend
cd vulcanlab_ui
npm install
cd ..
```

### Test 2: Run all verifications from Step 3-10
Follow each step in the implementation plan:
- Run test suite
- Test imports
- Test CLI commands
- Test API server
- Test frontend
- Run search script
- Review workspace files
- Generate report

### Test 3: Document results
Fill out the verification report with actual results.

### Test 4: Sign-off
If all checks pass, mark the rename as complete.

## Success criteria

- [ ] All unit tests pass: `pytest tests/unit/ -v`
- [ ] Import verification script passes
- [ ] At least 3 CLI commands tested and working
- [ ] API server starts without errors
- [ ] API docs accessible and show VulcanLab branding
- [ ] Frontend builds: `npm run build` succeeds
- [ ] Frontend runs: `npm run dev` succeeds
- [ ] UI loads in browser with VulcanLab branding
- [ ] Search script finds no inappropriate psychrag references
- [ ] Verification report created and all items checked
- [ ] Integration smoke test passes
- [ ] Package can be reinstalled: `pip install -e .` succeeds
- [ ] No ModuleNotFoundError for vulcanlab imports
- [ ] No remaining psychrag imports in source code
- [ ] End-to-end user workflow works (can run a query if applicable)

## Post-verification tasks

After this ticket is complete:

1. **Merge to main**: Merge the verification branch
2. **Tag release**: Consider tagging as v0.2.0 or similar to mark the rename
3. **Update deployment**: Update any CI/CD pipelines, Docker configs, etc. (separate task)
4. **User communication**: Notify users of the rename (separate task)
5. **Archive old docs**: Keep old documentation for reference if needed
6. **Monitor**: Watch for any rename-related issues in the first few days

## Notes

- This ticket is about verification, not implementation
- If verification fails, go back and fix the relevant ticket (T01-T04)
- The goal is confidence that the rename is complete and correct
- Document any edge cases or exceptions found during verification
