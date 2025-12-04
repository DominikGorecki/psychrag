# T04: Update documentation and user-facing text

## Context

- **PRD**: [prd-rename-vulcanlab.md](prd-rename-vulcanlab.md)
- **PRD Sections**: Phase 6 (Documentation), Requirements 4.3 (UI Text Content), Requirements 5 (Documentation)
- **User Value**: Completes the rebrand by updating all user-facing documentation, README, code comments, and UI text to reference VulcanLab instead of PsychRAG. Ensures users see consistent branding throughout their experience.

## Outcome

All documentation files reference VulcanLab, the README is updated with correct package names and commands, all UI text displays VulcanLab branding, code comments and docstrings use the new name, and the project presents a consistent brand identity.

## Scope

### In scope:
- Update `README.md` with VulcanLab branding and correct commands
- Update all documentation markdown files in `documentation/`
- Update user-facing text in UI components (page titles, headers, navigation labels)
- Update code comments and docstrings that mention PsychRAG
- Update CLI help text and error messages
- Update MkDocs documentation site configuration and content in `docs/`

### Out of scope:
- Core package rename - completed in T01
- API package rename - completed in T02
- Frontend package rename - completed in T03
- Configuration file names - not being renamed per user guidance
- Historical git commit messages - no need to rewrite history

## Implementation plan

### Documentation Updates

#### Step 1: Verify prerequisites
Before starting, ensure:
1. T01 (core package rename) is complete
2. T02 (API package rename) is complete
3. T03 (frontend package rename) is complete
4. You know the correct new module names and commands

#### Step 2: Create feature branch
```bash
git checkout -b feature/update-documentation
```

#### Step 3: Update README.md
The README is the primary user entry point. Update:

**Changes to make:**
1. **Project title**: "PsychRAG" → "VulcanLab"
2. **Description**: Update description if it mentions "psychology literature" (consider making it more general: "academic literature")
3. **Command examples**: Update all `python -m psychrag.*` → `python -m vulcanlab.*`
4. **Import examples**: Update all `from psychrag.*` → `from vulcanlab.*`
5. **Configuration file references**: Keep `psychrag.config.json` as-is (per user guidance)
6. **Directory paths**: Keep existing paths (not updating per user guidance)
7. **Package name**: Ensure it says "VulcanLab" (already in pyproject.toml)

**Specific sections to update:**
- Title at top: `# PsychRAG` → `# VulcanLab`
- Description: "A Retrieval-Augmented Generation system for psychology literature" → "A Retrieval-Augmented Generation workbench for academic literature"
- All CLI command examples in Setup section
- All import examples in code snippets
- Any references to package names

**Example changes:**
```markdown
<!-- Before -->
# PsychRAG
python -m psychrag.config.app_config_cli show
from psychrag.config import AppConfig

<!-- After -->
# VulcanLab
python -m vulcanlab.config.app_config_cli show
from vulcanlab.config import AppConfig
```

#### Step 4: Update documentation files
Update all `.md` files in `documentation/` directory:

**Search and replace patterns:**
- "PsychRAG" → "VulcanLab"
- "psychRAG" → "vulcanlab"
- "psychrag" → "vulcanlab" (where it refers to package name)
- `python -m psychrag.` → `python -m vulcanlab.`
- `from psychrag.` → `from vulcanlab.`
- `import psychrag` → `import vulcanlab`
- `psychrag_api` → `vulcanlab_api`
- `psychrag_ui` → `vulcanlab_ui`

**Documentation files to update:**
```bash
# Find all markdown files in documentation/
find documentation/ -name "*.md" -type f
```

**Key files (based on PRD):**
- `documentation/rename-to-vulcanlab.md` - Review and update if needed
- `documentation/rename-to-vulcanlab-checklist.md` - Review and mark items complete
- Any getting started guides
- Any API documentation
- Any development guides
- Any architecture documentation

**Preservation notes:**
- Keep historical context where appropriate
- If a document describes the rename process, keep mentions of "PsychRAG" where historically accurate
- Focus on current instructions and examples

#### Step 5: Update MkDocs documentation site
Update documentation in `docs/src/`:

**Files to update:**
- `docs/src/index.md` - Main landing page
- `docs/src/getting-started.md` - Getting started guide
- Any other `.md` files in `docs/src/`

**MkDocs config:**
- `docs/mkdocs.yml` - Already has `site_name: VulcanLab` ✓ (verify)

**Changes to make:**
Same patterns as Step 4:
- Update all command examples
- Update all import examples
- Update all references to package names

#### Step 6: Update code comments and docstrings
Search for "PsychRAG" in code comments:

```bash
# Find docstrings and comments mentioning PsychRAG
grep -r "PsychRAG" src/ --include="*.py"
grep -r "psychRAG" src/ --include="*.py"
```

**Update patterns:**
- Docstrings: `"""PsychRAG tool for..."""` → `"""VulcanLab tool for..."""`
- Comments: `# PsychRAG specific logic` → `# VulcanLab specific logic`
- Module docstrings at top of files

**Files likely to have docstrings:**
- `src/vulcanlab/__init__.py`
- `src/vulcanlab/config/app_config.py`
- All `*_cli.py` files (they may have help text)
- Main module files in each subpackage

#### Step 7: Update CLI help text
CLI commands often have help text shown to users. Update these:

**Files to check:**
- All files ending in `_cli.py` in `src/vulcanlab/`
- Look for `argparse` help strings
- Look for `click` command help decorators
- Look for manual help text strings

**Example:**
```python
# Before
parser.add_argument('--config', help='Path to PsychRAG config file')

# After
parser.add_argument('--config', help='Path to VulcanLab config file')
```

**Search command:**
```bash
grep -r "PsychRAG" src/vulcanlab/ --include="*_cli.py"
```

#### Step 8: Update UI user-facing text
Update text visible to users in the frontend:

**Files to check:**
- `vulcanlab_ui/src/app/**/*.tsx` - Page components
- `vulcanlab_ui/src/components/**/*.tsx` - Reusable components

**Elements to update:**
- Page titles: `<title>PsychRAG</title>` → `<title>VulcanLab</title>`
- Headers: `<h1>PsychRAG Dashboard</h1>` → `<h1>VulcanLab Dashboard</h1>`
- Navigation labels
- Button text (if it mentions the app name)
- Footer text
- Error messages that mention the app name
- Help text and tooltips

**Search command:**
```bash
cd vulcanlab_ui
grep -r "PsychRAG" src/ --include="*.tsx" --include="*.ts"
grep -r "psychRAG" src/ --include="*.tsx" --include="*.ts"
```

**Example changes:**
```tsx
// Before
<h1>Welcome to PsychRAG</h1>
<title>PsychRAG - RAG Workbench</title>

// After
<h1>Welcome to VulcanLab</h1>
<title>VulcanLab - RAG Workbench</title>
```

#### Step 9: Update API documentation metadata
If FastAPI has title/description in the app definition:

**File:** `src/vulcanlab_api/main.py`

```python
# Before
app = FastAPI(
    title="PsychRAG API",
    description="API for PsychRAG workbench"
)

# After
app = FastAPI(
    title="VulcanLab API",
    description="API for VulcanLab workbench"
)
```

This affects the auto-generated API docs at `/docs`.

#### Step 10: Verification checks
Run comprehensive searches for remaining references:

```bash
# Check for PsychRAG (various capitalizations)
grep -ri "psychrag" . --include="*.md" --include="*.py" --include="*.tsx" --include="*.ts" \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv

# Check README specifically
grep -i "psychrag" README.md

# Check docs
grep -ri "psychrag" docs/ --include="*.md"
grep -ri "psychrag" documentation/ --include="*.md"

# Check code comments
grep -r "PsychRAG" src/ --include="*.py"

# Check UI text
grep -r "PsychRAG" vulcanlab_ui/src/ --include="*.tsx"
```

**Note**: Some results are expected:
- Historical documentation about the rename itself
- Config filename `psychrag.config.json` (not being renamed)
- Git history (don't need to change)

### Unit tests

Since this is primarily documentation and text updates, tests focus on verification:

#### Test 1: README validation
**Manual verification:**
- Open `README.md`
- Search for "psychrag" (case-insensitive)
- Verify all code examples use `vulcanlab`
- Verify title is "VulcanLab"

#### Test 2: Documentation build (MkDocs)
If MkDocs is set up:
```bash
cd docs
mkdocs build
```
**Expected outcome**: Documentation builds without errors

#### Test 3: CLI help text verification
Run CLI commands with `--help` and verify output:
```bash
python -m vulcanlab.config.app_config_cli --help
python -m vulcanlab.data.init_db --help
# Check help text says "VulcanLab" not "PsychRAG"
```

#### Test 4: API docs title verification
Start the API and check the docs page:
```bash
python -m vulcanlab_api
# Visit http://localhost:8000/docs
```
**Expected**: Page title shows "VulcanLab API" not "PsychRAG API"

#### Test 5: UI text verification
Start the UI and check visible text:
```bash
cd vulcanlab_ui
npm run dev
# Visit http://localhost:3000
```
**Expected**:
- Browser tab title shows "VulcanLab"
- Page headers show "VulcanLab"
- No visible "PsychRAG" text

### Automated check script
Create a verification script to catch missed references:

**File:** `scripts/verify_rename.sh` (or `.bat` for Windows)
```bash
#!/bin/bash
echo "Checking for remaining PsychRAG references..."

# Check README
echo "=== README ==="
grep -in "psychrag" README.md || echo "✓ Clean"

# Check documentation
echo "=== Documentation ==="
grep -rin "psychrag" documentation/ --include="*.md" | grep -v "rename-to-vulcanlab" || echo "✓ Clean"

# Check code comments
echo "=== Code comments ==="
grep -rn "PsychRAG" src/ --include="*.py" || echo "✓ Clean"

# Check UI text
echo "=== UI text ==="
grep -rn "PsychRAG" vulcanlab_ui/src/ --include="*.tsx" --include="*.ts" || echo "✓ Clean"

echo "Done"
```

## Dependencies and sequencing

### Dependencies:
- **Prerequisite**: T01 (core package rename) completed
- **Prerequisite**: T02 (API package rename) completed
- **Prerequisite**: T03 (frontend package rename) completed
- **Blocks**: T05 (final verification) - Should be done before final checks

### Sequencing notes:
- This ticket should be done AFTER T01, T02, and T03 are complete
- Ensures all code examples in documentation are accurate
- Can be done in parallel with parts of T05, but T05 final checks should wait for T04
- Consider doing this work in a feature branch

## Clarifications and assumptions

### Assumptions:
1. **Config filename stays**: References to `psychrag.config.json` should remain unchanged
2. **Historical context preserved**: Documentation about the rename itself can mention "PsychRAG" historically
3. **MkDocs is used**: The `docs/` directory is for MkDocs documentation
4. **UI uses standard React patterns**: Text is in JSX/TSX files, not separate i18n files
5. **No translation files**: Assuming English-only, no i18n files to update

### Questions (NOT blocking):
- Are there any external wikis, Notion docs, or other documentation outside the repo?
- Are there any video tutorials or screenshots that show "PsychRAG"?
- Is there a blog or website that needs updating?

### Pre-implementation checklist:
> **Before implementing, review the following:**
> 1. Confirm T01, T02, and T03 are complete and merged
> 2. Understand which references should be kept (config filenames, historical docs)
> 3. Have a list of all documentation locations (README, docs/, documentation/, UI)
> 4. Know whether to keep "psychology" focus or change to "academic literature"

## Manual test plan

After implementation, manually verify:

### Test 1: README review
```bash
# Open and read README.md
code README.md
# Verify:
# - Title is "VulcanLab"
# - All commands use vulcanlab
# - All imports use vulcanlab
# - Description updated appropriately
```

### Test 2: Documentation site build
```bash
cd docs
mkdocs build
mkdocs serve
# Visit http://127.0.0.1:8000
# Verify site shows "VulcanLab" branding
```

### Test 3: CLI help text
```bash
python -m vulcanlab.config.app_config_cli --help
# Verify help text mentions "VulcanLab" if applicable
# Check several CLI commands
```

### Test 4: API documentation
```bash
python -m vulcanlab_api
# Visit http://localhost:8000/docs
# Verify:
# - Title is "VulcanLab API"
# - Description mentions VulcanLab
```

### Test 5: UI text visual inspection
```bash
cd vulcanlab_ui
npm run dev
# Visit http://localhost:3000
# Check:
# - Browser tab title
# - Page header
# - Navigation menu
# - Footer
# - Any help text or tooltips
```

### Test 6: Search for remaining references
```bash
# Run verification script
bash scripts/verify_rename.sh

# Or manual searches:
grep -ri "psychrag" README.md
grep -ri "psychrag" documentation/ --include="*.md"
grep -r "PsychRAG" src/vulcanlab/ --include="*.py"
grep -r "PsychRAG" vulcanlab_ui/src/ --include="*.tsx"
```

### Test 7: Code comment review
Pick a few key files and review docstrings:
```bash
# Check main config file
cat src/vulcanlab/config/app_config.py | grep -i "psychrag"
# Should be empty or only in context of reading psychrag.config.json

# Check main __init__ file
cat src/vulcanlab/__init__.py | head -20
# Should have VulcanLab in module docstring
```

## Success criteria

- [ ] README.md title is "VulcanLab"
- [ ] README.md description updated (if changing from "psychology" to "academic")
- [ ] All README.md code examples use `vulcanlab` package name
- [ ] All documentation in `documentation/` updated
- [ ] All documentation in `docs/src/` updated
- [ ] MkDocs site builds and shows VulcanLab branding
- [ ] Code comments and docstrings reference VulcanLab
- [ ] CLI help text uses VulcanLab name (where applicable)
- [ ] UI page titles show "VulcanLab"
- [ ] UI headers and navigation show "VulcanLab"
- [ ] API documentation at `/docs` shows "VulcanLab API"
- [ ] No inappropriate "PsychRAG" references in user-facing text
- [ ] Verification script runs clean (expected exceptions only)
- [ ] Search for "psychrag" returns only: config filename, historical docs, git history
