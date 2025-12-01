# Migration Guide: Renaming psychRAG to VulcanLab

**Date:** 2025-01-XX  
**Purpose:** Comprehensive guide for renaming the project from "psychRAG" to "VulcanLab"  
**Estimated Effort:** 4-6 hours for complete migration  
**Risk Level:** Medium (requires careful coordination and testing)

---

## Table of Contents

1. [Overview](#overview)
2. [Scope of Changes](#scope-of-changes)
3. [Pre-Migration Checklist](#pre-migration-checklist)
4. [Directory Structure Changes](#directory-structure-changes)
5. [Python Package Changes](#python-package-changes)
6. [Import Statement Changes](#import-statement-changes)
7. [Configuration Files](#configuration-files)
8. [Frontend Changes](#frontend-changes)
9. [Database Changes](#database-changes)
10. [Documentation Updates](#documentation-updates)
11. [Testing Considerations](#testing-considerations)
12. [Step-by-Step Migration Process](#step-by-step-migration-process)
13. [Post-Migration Verification](#post-migration-verification)
14. [Rollback Plan](#rollback-plan)

---

## Overview

This document outlines all changes required to rename the project from **psychRAG** to **VulcanLab**. The renaming affects:

- **Package names**: `psychrag` → `vulcanlab`
- **API package**: `psychrag_api` → `vulcanlab_api`
- **UI package**: `psychrag_ui` → `vulcanlab_ui`
- **Configuration files**: `psychrag.config.json` → `vulcanlab.config.json`
- **Database names**: `psych_rag_test` → `vulcanlab_test`
- **All documentation and references**

### Naming Conventions

- **Package name**: `vulcanlab` (lowercase, no underscores)
- **Display name**: `VulcanLab` (PascalCase)
- **API package**: `vulcanlab_api` (lowercase with underscore)
- **UI package**: `vulcanlab_ui` (lowercase with underscore)
- **Database**: `vulcanlab_test` (lowercase with underscore)

---

## Scope of Changes

### Files Requiring Changes

Based on codebase analysis, approximately **141 files** contain references to "psychrag" or "psychRAG" that need updating:

#### Categories:

1. **Python Source Code** (~90 files)
   - Package directories: `src/psychrag/` → `src/vulcanlab/`
   - API package: `src/psychrag_api/` → `src/vulcanlab_api/`
   - All import statements
   - Module docstrings
   - CLI command examples

2. **Configuration Files** (3 files)
   - `pyproject.toml`
   - `psychrag.config.json` → `vulcanlab.config.json`
   - `.env` files (if they reference package names)

3. **Frontend Code** (~10 files)
   - `psychrag_ui/` directory → `vulcanlab_ui/`
   - `package.json`
   - UI component text and titles
   - API endpoint references

4. **Documentation** (~30 files)
   - README files
   - Documentation markdown files
   - Code examples
   - Project structure documentation

5. **Test Files** (~15 files)
   - Import statements
   - Test module names

6. **Build Artifacts** (will be regenerated)
   - `src/psychrag.egg-info/` → `src/vulcanlab.egg-info/`
   - `__pycache__/` directories

---

## Pre-Migration Checklist

Before starting the migration:

- [ ] **Create a backup branch**: `git checkout -b backup/pre-rename`
- [ ] **Commit all current work**: Ensure working directory is clean
- [ ] **Create migration branch**: `git checkout -b feature/rename-to-vulcanlab`
- [ ] **Document current state**: Note any uncommitted changes
- [ ] **Backup database**: Export current database schema and data
- [ ] **Notify team**: Inform all developers about the migration
- [ ] **Test suite passes**: Ensure all tests pass before migration
- [ ] **Documentation snapshot**: Save current documentation state

---

## Directory Structure Changes

### Current Structure
```
psychRAG-test/
├── src/
│   ├── psychrag/              # Main package
│   └── psychrag_api/          # API package
├── psychrag_ui/               # Frontend UI
├── psychrag.config.json       # Config file
└── ...
```

### Target Structure
```
vulcanlab-test/                # Optional: rename root directory
├── src/
│   ├── vulcanlab/             # Main package (renamed)
│   └── vulcanlab_api/         # API package (renamed)
├── vulcanlab_ui/              # Frontend UI (renamed)
├── vulcanlab.config.json      # Config file (renamed)
└── ...
```

### Directory Renaming Steps

1. **Rename main package directory**:
   ```bash
   mv src/psychrag src/vulcanlab
   ```

2. **Rename API package directory**:
   ```bash
   mv src/psychrag_api src/vulcanlab_api
   ```

3. **Rename UI directory**:
   ```bash
   mv psychrag_ui vulcanlab_ui
   ```

4. **Rename config file**:
   ```bash
   mv psychrag.config.json vulcanlab.config.json
   ```

5. **Clean build artifacts** (will be regenerated):
   ```bash
   rm -rf src/psychrag.egg-info/
   find . -type d -name __pycache__ -exec rm -r {} +
   find . -type f -name "*.pyc" -delete
   ```

---

## Python Package Changes

### 1. Package Name in `pyproject.toml`

**File**: `pyproject.toml`

**Current**:
```toml
[project]
name = "psychrag"
version = "0.1.0"
description = "A Retrieval-Augmented Generation system for psychology literature"
```

**Change to**:
```toml
[project]
name = "vulcanlab"
version = "0.1.0"
description = "VulcanLab - A Retrieval-Augmented Generation system"
```

### 2. Package `__init__.py` Files

**File**: `src/vulcanlab/__init__.py`

**Current**:
```python
"""
PsychRAG - A Retrieval-Augmented Generation system for psychology literature.
"""

__version__ = "0.1.0"
```

**Change to**:
```python
"""
VulcanLab - A Retrieval-Augmented Generation system.
"""

__version__ = "0.1.0"
```

**File**: `src/vulcanlab_api/__init__.py`

**Current**:
```python
"""
PsychRAG API - FastAPI REST interface for the PsychRAG system.
...
"""

__version__ = "0.1.0"
```

**Change to**:
```python
"""
VulcanLab API - FastAPI REST interface for the VulcanLab system.
...
"""

__version__ = "0.1.0"
```

### 3. Module Docstrings

All module docstrings containing "psychRAG" or "PsychRAG" need updating. Examples:

**Files to update**:
- `src/vulcanlab/config/__init__.py` - "Configuration management for psychrag"
- `src/vulcanlab/__init__.py` - Package description
- All CLI module docstrings
- All library module docstrings

**Search pattern**: `psychrag|psychRAG|PsychRAG` → `vulcanlab|VulcanLab`

---

## Import Statement Changes

### Import Pattern Changes

All import statements need to be updated from `psychrag` to `vulcanlab`:

#### 1. Library Imports

**Current**:
```python
from psychrag.chunking import chunk_headings
from psychrag.retrieval import retrieve
from psychrag.conversions.conv_pdf2md import convert_pdf_to_markdown
```

**Change to**:
```python
from vulcanlab.chunking import chunk_headings
from vulcanlab.retrieval import retrieve
from vulcanlab.conversions.conv_pdf2md import convert_pdf_to_markdown
```

#### 2. API Router Imports

**Current**:
```python
from psychrag.data.database import get_session
from psychrag.data.models import Work
from psychrag.sanitization import extract_titles_from_work
```

**Change to**:
```python
from vulcanlab.data.database import get_session
from vulcanlab.data.models import Work
from vulcanlab.sanitization import extract_titles_from_work
```

#### 3. CLI Module Imports

**Current**:
```python
from psychrag.chunking.chunk_headings import chunk_headings
from psychrag.data.database import get_session
```

**Change to**:
```python
from vulcanlab.chunking.chunk_headings import chunk_headings
from vulcanlab.data.database import get_session
```

#### 4. Test Imports

**Current**:
```python
from psychrag.data.models import Work
from psychrag.conversions.conv_pdf2md import convert_pdf_to_markdown
```

**Change to**:
```python
from vulcanlab.data.models import Work
from vulcanlab.conversions.conv_pdf2md import convert_pdf_to_markdown
```

### Automated Import Replacement

Use find-and-replace with regex:

**Pattern**: `from psychrag\.` → `from vulcanlab.`  
**Pattern**: `import psychrag\.` → `import vulcanlab.`  
**Pattern**: `psychrag\.` → `vulcanlab.`

**Files affected**: ~90 Python files

---

## Configuration Files

### 1. `pyproject.toml`

**Changes required**:
- Package name: `psychrag` → `vulcanlab`
- Description text updates

### 2. `psychrag.config.json` → `vulcanlab.config.json`

**File rename**: `psychrag.config.json` → `vulcanlab.config.json`

**Current content**:
```json
{
  "database": {
    "db_name": "psych_rag_test",
    "app_user": "psych_rag_app_user_test"
  },
  "paths": {
    "input_dir": "D:\\psychRAG_data\\input",
    "output_dir": "D:\\psychRAG_data\\output"
  }
}
```

**Update database names** (optional but recommended):
```json
{
  "database": {
    "db_name": "vulcanlab_test",
    "app_user": "vulcanlab_app_user_test"
  },
  "paths": {
    "input_dir": "D:\\VulcanLab_data\\input",
    "output_dir": "D:\\VulcanLab_data\\output"
  }
}
```

**Note**: Path updates are optional - only change if you want to rename data directories.

### 3. Code References to Config File

**Files that reference `psychrag.config.json`**:
- `src/vulcanlab/config/app_config.py` - `get_config_path()` function
- `src/vulcanlab_api/routers/settings.py` - Documentation
- `README.md` - Documentation
- `psychrag_ui/src/app/settings/page.tsx` - UI text

**Search pattern**: `psychrag\.config\.json` → `vulcanlab.config.json`

### 4. Environment Variables

Check `.env` files for any references to:
- Database names
- Path references
- Package names

---

## Frontend Changes

### 1. Directory Rename

**Rename**: `psychrag_ui/` → `vulcanlab_ui/`

### 2. `package.json`

**File**: `vulcanlab_ui/package.json`

**Current**:
```json
{
  "name": "psychrag_ui",
  "version": "0.1.0",
  ...
}
```

**Change to**:
```json
{
  "name": "vulcanlab_ui",
  "version": "0.1.0",
  ...
}
```

### 3. UI Component Text

**Files to update**:

**`vulcanlab_ui/src/app/layout.tsx`**:
```tsx
// Current
title: "PsychRAG UI",
description: "Interface for PsychRAG System",

// Change to
title: "VulcanLab UI",
description: "Interface for VulcanLab System",
```

**`vulcanlab_ui/src/components/nav-bar.tsx`**:
```tsx
// Current
<h1>PsychRAG UI</h1>

// Change to
<h1>VulcanLab UI</h1>
```

**`vulcanlab_ui/src/app/page.tsx`**:
```tsx
// Current
<CardTitle>Welcome to PsychRAG</CardTitle>

// Change to
<CardTitle>Welcome to VulcanLab</CardTitle>
```

**`vulcanlab_ui/src/app/settings/page.tsx`**:
```tsx
// Current
PostgreSQL connection configuration. Changes are saved to psychrag.config.json.

// Change to
PostgreSQL connection configuration. Changes are saved to vulcanlab.config.json.
```

### 4. API Endpoint References

If the frontend hardcodes API paths, check for:
- `/api/psychrag/` → `/api/vulcanlab/` (if applicable)
- API base URL references

**Note**: API endpoints themselves don't need to change (they're `/conv`, `/rag`, etc.), but any references in frontend code should be updated.

### 5. Frontend Build

After changes:
```bash
cd vulcanlab_ui
npm install  # Reinstall if package.json changed
npm run build
```

---

## Database Changes

### Database Name Changes

**Current database names**:
- `psych_rag_test` (main database)
- `psych_rag_app_user_test` (application user)

**New database names** (optional):
- `vulcanlab_test` (main database)
- `vulcanlab_app_user_test` (application user)

### Migration Steps

#### Option 1: Rename Existing Database (Recommended for Development)

```sql
-- 1. Rename database
ALTER DATABASE psych_rag_test RENAME TO vulcanlab_test;

-- 2. Rename user (if exists)
ALTER USER psych_rag_app_user_test RENAME TO vulcanlab_app_user_test;

-- 3. Update grants
REASSIGN OWNED BY psych_rag_app_user_test TO vulcanlab_app_user_test;
```

#### Option 2: Create New Database (Recommended for Production)

```sql
-- 1. Create new database
CREATE DATABASE vulcanlab_test;

-- 2. Create new user
CREATE USER vulcanlab_app_user_test WITH PASSWORD 'your_password';

-- 3. Grant privileges
GRANT ALL PRIVILEGES ON DATABASE vulcanlab_test TO vulcanlab_app_user_test;

-- 4. Migrate data (using pg_dump/pg_restore)
pg_dump -U postgres psych_rag_test > backup.sql
psql -U postgres vulcanlab_test < backup.sql
```

### Update Database Configuration

After database changes, update:
1. `vulcanlab.config.json` - Database name and user
2. `.env` file - Database connection strings (if used)
3. Connection strings in code (if hardcoded)

### Database Connection Code

**File**: `src/vulcanlab/data/database.py`

Check for hardcoded database names:
```python
# Search for: psych_rag_test, psych_rag_app_user_test
# Update if found
```

---

## Documentation Updates

### Files Requiring Updates

#### 1. README.md

**Current**: Multiple references to "PsychRAG" and "psychrag"

**Updates needed**:
- Title: `# PsychRAG` → `# VulcanLab`
- All command examples: `python -m psychrag.` → `python -m vulcanlab.`
- Config file references: `psychrag.config.json` → `vulcanlab.config.json`
- Package references throughout

#### 2. Project Structure Documentation

**Files**:
- `project-structure.md`
- `.cursorrules`
- `.claude/instructions.md`

**Updates**:
- `psychrag/` → `vulcanlab/`
- `psychRAG/` → `VulcanLab`
- All code examples

#### 3. API Documentation

**File**: `src/vulcanlab_api/README.md`

**Updates**:
- Title and description
- Package name references
- Command examples

#### 4. Module Documentation

**Files**: All `README.md` files in module directories

**Search pattern**: `psychrag|psychRAG|PsychRAG` → `vulcanlab|VulcanLab`

#### 5. Documentation Folder

**Files in `documentation/`**:
- `pre-release-audit.md`
- `augmentation.md`
- `retrieval.md`
- `breadcrumb-refactoring-plan.md`
- All files in `documentation/work/`

**Updates**: Replace all references to psychRAG/PsychRAG

### Documentation Search Pattern

Use find-and-replace across documentation:

**Patterns**:
- `psychRAG` → `VulcanLab`
- `PsychRAG` → `VulcanLab`
- `psychrag` → `vulcanlab`
- `psychrag.config.json` → `vulcanlab.config.json`
- `python -m psychrag.` → `python -m vulcanlab.`

---

## Testing Considerations

### Test File Updates

**All test files** need import statement updates:

**Current**:
```python
from psychrag.data.models import Work
from psychrag.conversions import convert_pdf_to_markdown
```

**Change to**:
```python
from vulcanlab.data.models import Work
from vulcanlab.conversions import convert_pdf_to_markdown
```

### Test Execution Commands

**Current**:
```bash
venv\Scripts\pytest
```

**After migration**: Same (pytest discovers tests automatically)

### Test Configuration

**File**: `pyproject.toml`

**Current**:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

**After migration**: Same (no changes needed)

### Verification Tests

After migration, run:

```bash
# 1. Install renamed package
venv\Scripts\pip install -e .

# 2. Run all tests
venv\Scripts\pytest

# 3. Test imports
venv\Scripts\python -c "import vulcanlab; print(vulcanlab.__version__)"
venv\Scripts\python -c "import vulcanlab_api; print(vulcanlab_api.__version__)"

# 4. Test CLI commands
venv\Scripts\python -m vulcanlab.config.app_config_cli show
```

---

## Step-by-Step Migration Process

### Phase 1: Preparation (30 minutes)

1. **Create backup branch**
   ```bash
   git checkout -b backup/pre-rename
   git push origin backup/pre-rename
   ```

2. **Create migration branch**
   ```bash
   git checkout -b feature/rename-to-vulcanlab
   ```

3. **Document current state**
   - Note any uncommitted changes
   - Export database schema
   - Take screenshots of UI (if needed)

### Phase 2: Directory Renaming (15 minutes)

1. **Rename directories**
   ```bash
   mv src/psychrag src/vulcanlab
   mv src/psychrag_api src/vulcanlab_api
   mv psychrag_ui vulcanlab_ui
   mv psychrag.config.json vulcanlab.config.json
   ```

2. **Clean build artifacts**
   ```bash
   rm -rf src/psychrag.egg-info/
   find . -type d -name __pycache__ -exec rm -r {} +
   ```

3. **Commit directory changes**
   ```bash
   git add -A
   git commit -m "Rename directories: psychrag -> vulcanlab"
   ```

### Phase 3: Python Package Updates (60 minutes)

1. **Update `pyproject.toml`**
   - Change package name
   - Update description

2. **Update package `__init__.py` files**
   - `src/vulcanlab/__init__.py`
   - `src/vulcanlab_api/__init__.py`

3. **Update all import statements**
   - Use IDE find-and-replace: `from psychrag.` → `from vulcanlab.`
   - Use IDE find-and-replace: `import psychrag.` → `import vulcanlab.`
   - Verify no remaining `psychrag.` imports

4. **Update module docstrings**
   - Search: `psychrag|psychRAG|PsychRAG`
   - Replace with: `vulcanlab|VulcanLab`

5. **Test imports**
   ```bash
   venv\Scripts\pip install -e .
   venv\Scripts\python -c "import vulcanlab; import vulcanlab_api"
   ```

6. **Commit Python changes**
   ```bash
   git add -A
   git commit -m "Update Python package names and imports"
   ```

### Phase 4: Configuration Files (15 minutes)

1. **Update `vulcanlab.config.json`**
   - Rename file (already done)
   - Update database names (optional)
   - Update path references (optional)

2. **Update config file references in code**
   - Search: `psychrag.config.json`
   - Replace: `vulcanlab.config.json`

3. **Update `.env` files** (if applicable)
   - Check for database name references

4. **Commit configuration changes**
   ```bash
   git add -A
   git commit -m "Update configuration files"
   ```

### Phase 5: Frontend Updates (30 minutes)

1. **Update `vulcanlab_ui/package.json`**
   - Change package name

2. **Update UI component text**
   - `layout.tsx` - Title and description
   - `nav-bar.tsx` - Brand name
   - `page.tsx` - Welcome text
   - `settings/page.tsx` - Config file references

3. **Test frontend build**
   ```bash
   cd vulcanlab_ui
   npm install
   npm run build
   ```

4. **Commit frontend changes**
   ```bash
   git add -A
   git commit -m "Update frontend package name and UI text"
   ```

### Phase 6: Database Updates (30 minutes)

1. **Backup current database**
   ```bash
   pg_dump -U postgres psych_rag_test > backup_psych_rag.sql
   ```

2. **Rename database** (development) or create new (production)
   ```sql
   -- Development: Rename
   ALTER DATABASE psych_rag_test RENAME TO vulcanlab_test;
   
   -- OR Production: Create new
   CREATE DATABASE vulcanlab_test;
   -- Then restore from backup
   ```

3. **Update `vulcanlab.config.json`**
   - Update database name
   - Update app user name

4. **Test database connection**
   ```bash
   venv\Scripts\python -c "from vulcanlab.data.database import get_session; get_session()"
   ```

5. **Commit database config changes**
   ```bash
   git add vulcanlab.config.json
   git commit -m "Update database configuration"
   ```

### Phase 7: Documentation Updates (60 minutes)

1. **Update README.md**
   - Title
   - All command examples
   - Config file references

2. **Update project structure docs**
   - `project-structure.md`
   - `.cursorrules`
   - `.claude/instructions.md`

3. **Update API documentation**
   - `src/vulcanlab_api/README.md`

4. **Update module documentation**
   - All `README.md` files in modules

5. **Update documentation folder**
   - All files in `documentation/`
   - Use find-and-replace across all `.md` files

6. **Commit documentation**
   ```bash
   git add -A
   git commit -m "Update all documentation references"
   ```

### Phase 8: Testing and Verification (60 minutes)

1. **Run test suite**
   ```bash
   venv\Scripts\pytest
   ```

2. **Test CLI commands**
   ```bash
   venv\Scripts\python -m vulcanlab.config.app_config_cli show
   venv\Scripts\python -m vulcanlab.data.init_db -v
   ```

3. **Test API**
   ```bash
   venv\Scripts\python -m vulcanlab_api
   # Visit http://localhost:8000/docs
   ```

4. **Test frontend**
   ```bash
   cd vulcanlab_ui
   npm run dev
   # Visit http://localhost:3000
   ```

5. **Fix any issues found**

6. **Commit fixes**
   ```bash
   git add -A
   git commit -m "Fix migration issues"
   ```

### Phase 9: Final Verification (30 minutes)

1. **Run comprehensive search**
   ```bash
   # Search for any remaining psychrag references
   grep -r "psychrag" --exclude-dir=venv --exclude-dir=node_modules --exclude-dir=.git .
   grep -r "psychRAG" --exclude-dir=venv --exclude-dir=node_modules --exclude-dir=.git .
   ```

2. **Verify no broken imports**
   ```bash
   venv\Scripts\python -c "import vulcanlab; import vulcanlab_api"
   ```

3. **Check build artifacts**
   ```bash
   ls src/vulcanlab.egg-info/  # Should exist after pip install -e .
   ```

4. **Final commit**
   ```bash
   git add -A
   git commit -m "Complete migration: psychRAG -> VulcanLab"
   ```

---

## Post-Migration Verification

### Checklist

- [ ] **Package installation works**
  ```bash
  venv\Scripts\pip install -e .
  venv\Scripts\python -c "import vulcanlab; print(vulcanlab.__version__)"
  ```

- [ ] **All imports work**
  ```bash
  venv\Scripts\python -c "from vulcanlab.chunking import chunk_headings"
  venv\Scripts\python -c "from vulcanlab_api.main import app"
  ```

- [ ] **CLI commands work**
  ```bash
  venv\Scripts\python -m vulcanlab.config.app_config_cli show
  ```

- [ ] **API starts successfully**
  ```bash
  venv\Scripts\python -m vulcanlab_api
  # Check http://localhost:8000/docs
  ```

- [ ] **Frontend builds and runs**
  ```bash
  cd vulcanlab_ui
  npm run build
  npm run dev
  ```

- [ ] **Database connection works**
  ```bash
  venv\Scripts\python -c "from vulcanlab.data.database import get_session; session = get_session(); session.close()"
  ```

- [ ] **All tests pass**
  ```bash
  venv\Scripts\pytest
  ```

- [ ] **No remaining references**
  ```bash
  grep -r "psychrag" --exclude-dir=venv --exclude-dir=node_modules --exclude-dir=.git .
  grep -r "psychRAG" --exclude-dir=venv --exclude-dir=node_modules --exclude-dir=.git .
  ```

- [ ] **Documentation is updated**
  - README.md
  - All documentation files
  - Code examples

- [ ] **Configuration files updated**
  - `vulcanlab.config.json` exists
  - No references to `psychrag.config.json`

---

## Rollback Plan

If migration needs to be rolled back:

### Quick Rollback (Git)

```bash
# 1. Switch back to original branch
git checkout main  # or your original branch

# 2. Delete migration branch (optional)
git branch -D feature/rename-to-vulcanlab
```

### Database Rollback

```sql
-- If database was renamed
ALTER DATABASE vulcanlab_test RENAME TO psych_rag_test;

-- If new database was created, restore from backup
DROP DATABASE vulcanlab_test;
pg_restore -U postgres -d psych_rag_test backup_psych_rag.sql
```

### File System Rollback

If directories were renamed manually:
```bash
mv src/vulcanlab src/psychrag
mv src/vulcanlab_api src/psychrag_api
mv vulcanlab_ui psychrag_ui
mv vulcanlab.config.json psychrag.config.json
```

### Package Rollback

```bash
# Uninstall renamed package
venv\Scripts\pip uninstall vulcanlab

# Reinstall original (if backup branch checked out)
venv\Scripts\pip install -e .
```

---

## Common Issues and Solutions

### Issue 1: Import Errors After Migration

**Symptoms**: `ModuleNotFoundError: No module named 'psychrag'`

**Solution**:
1. Verify directory was renamed: `ls src/vulcanlab`
2. Reinstall package: `pip install -e .`
3. Check Python path: `python -c "import sys; print(sys.path)"`
4. Verify imports use `vulcanlab` not `psychrag`

### Issue 2: Config File Not Found

**Symptoms**: `FileNotFoundError: psychrag.config.json`

**Solution**:
1. Verify file was renamed: `ls vulcanlab.config.json`
2. Check `get_config_path()` function in `vulcanlab/config/app_config.py`
3. Update any hardcoded paths

### Issue 3: Database Connection Fails

**Symptoms**: `psycopg.OperationalError: database "psych_rag_test" does not exist`

**Solution**:
1. Verify database was renamed: `psql -U postgres -l`
2. Update `vulcanlab.config.json` with new database name
3. Check `.env` file for connection strings

### Issue 4: Frontend Build Fails

**Symptoms**: Build errors or missing modules

**Solution**:
1. Delete `node_modules` and `package-lock.json`
2. Update `package.json` name
3. Run `npm install`
4. Check for hardcoded API paths

### Issue 5: Tests Fail

**Symptoms**: Import errors in tests

**Solution**:
1. Update all test imports to use `vulcanlab`
2. Verify `pythonpath` in `pyproject.toml` points to `src`
3. Reinstall package: `pip install -e .`

---

## Estimated Time Breakdown

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 1 | Preparation | 30 min |
| 2 | Directory Renaming | 15 min |
| 3 | Python Package Updates | 60 min |
| 4 | Configuration Files | 15 min |
| 5 | Frontend Updates | 30 min |
| 6 | Database Updates | 30 min |
| 7 | Documentation Updates | 60 min |
| 8 | Testing and Verification | 60 min |
| 9 | Final Verification | 30 min |
| **Total** | | **~5 hours** |

**Buffer time**: Add 1-2 hours for unexpected issues

**Total estimated time**: 4-6 hours

---

## Additional Considerations

### Git History

The migration will preserve git history. Directory renames are tracked by Git, so:
- `git log --follow src/vulcanlab/file.py` will show history
- Blame and history remain intact

### CI/CD Pipeline

If you have CI/CD pipelines, update:
- Package names in build scripts
- Test commands
- Deployment configurations

### External Dependencies

Check for external references:
- Docker images/containers
- Deployment scripts
- Documentation sites
- Package registries (if published)

### Team Communication

Notify team members about:
- Branch name changes
- New package installation: `pip install -e .`
- Updated CLI commands
- Database migration requirements

---

## Conclusion

This migration guide provides a comprehensive roadmap for renaming psychRAG to VulcanLab. Follow the phases sequentially, test thoroughly at each step, and maintain backups throughout the process.

**Key Success Factors**:
1. ✅ Complete all phases in order
2. ✅ Test after each major change
3. ✅ Commit frequently
4. ✅ Verify no remaining references
5. ✅ Document any deviations from this guide

**Questions or Issues?**
- Review the "Common Issues" section
- Check git history for what changed
- Verify all imports and references
- Test in isolated environment first

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-XX  
**Author**: Migration Guide  
**Status**: Ready for Use

