# Rename PsychRAG to VulcanLab - Product Requirements Document

## Overview

This PRD outlines the requirements for renaming the entire project from "PsychRAG" to "VulcanLab". This is a comprehensive rebranding effort that touches all aspects of the system including:

- Python package names and module structure
- Database naming conventions
- Configuration files
- UI/Frontend application
- Documentation
- File system paths and directories
- Git repository metadata

## Current State Analysis

### Project Structure
The project consists of:
1. **Python Backend**: RAG (Retrieval-Augmented Generation) workbench for academic literature
2. **FastAPI Server**: API layer (`psychrag_api`)
3. **Next.js Frontend**: React-based UI (`psychrag_ui`)
4. **PostgreSQL Database**: With schema named around "psych_rag"
5. **Configuration System**: JSON config files and environment variables

### Scope of Changes
Based on codebase analysis:
- **838 occurrences** of "psychrag"/"PsychRAG" across **100+ files**
- **Core modules**: `src/psychrag/` and `src/psychrag_api/`
- **UI package**: `psychrag_ui/`
- **Database names**: `psych_rag_test`, `psych_rag_app_user_test`
- **Config files**: `psychrag.config.json`
- **File paths**: References to `psychRAG_data` directories

## Goals

### Primary Goals
1. Complete rebrand from PsychRAG to VulcanLab across all code, documentation, and configuration
2. Maintain backward compatibility where possible (database migration path)
3. Ensure all functionality continues to work post-rename
4. Update all user-facing text and documentation

### Non-Goals
- Changing the core functionality or features
- Modifying the API structure beyond naming
- Database schema changes (beyond renaming)

## Requirements

### 1. Python Package Renaming

#### 1.1 Core Package Structure
- **Current**: `src/psychrag/`
- **New**: `src/vulcanlab/`

**Submodules to rename:**
- `psychrag.ai` → `vulcanlab.ai`
- `psychrag.augmentation` → `vulcanlab.augmentation`
- `psychrag.chunking` → `vulcanlab.chunking`
- `psychrag.config` → `vulcanlab.config`
- `psychrag.conversions` → `vulcanlab.conversions`
- `psychrag.data` → `vulcanlab.data`
- `psychrag.retrieval` → `vulcanlab.retrieval`
- `psychrag.sanitization` → `vulcanlab.sanitization`
- `psychrag.utils` → `vulcanlab.utils`
- `psychrag.vectorization` → `vulcanlab.vectorization`

#### 1.2 API Package
- **Current**: `src/psychrag_api/`
- **New**: `src/vulcanlab_api/`

#### 1.3 Import Statements
Update all Python import statements:
```python
# Before
from psychrag.config import AppConfig
from psychrag_api.dependencies import get_db

# After
from vulcanlab.config import AppConfig
from vulcanlab_api.dependencies import get_db
```

#### 1.4 Module References
Update all `python -m` CLI commands in documentation:
```bash
# Before
python -m psychrag.config.app_config_cli show
python -m psychrag.data.init_db -v
python -m psychrag.conversions.conv_pdf2md

# After
python -m vulcanlab.config.app_config_cli show
python -m vulcanlab.data.init_db -v
python -m vulcanlab.conversions.conv_pdf2md
```

### 2. Configuration Files

#### 2.1 Main Configuration File
- **Current**: `psychrag.config.json`
- **New**: `vulcanlab.config.json`

**Content Updates:**
```json
{
  "database": {
    "db_name": "vulcanlab_test",        // was: psych_rag_test
    "app_user": "vulcanlab_app_user"    // was: psych_rag_app_user_test
  },
  "paths": {
    "input_dir": "D:\\vulcanlab_data\\input",    // was: psychRAG_data
    "output_dir": "D:\\vulcanlab_data\\output"
  }
}
```

#### 2.2 Environment Variables
Update `.env` variable names:
```bash
# Before
POSTGRES_APP_PASSWORD=psych_rag_secure_password

# After
POSTGRES_APP_PASSWORD=vulcanlab_secure_password
```

#### 2.3 pyproject.toml
Already shows `name = "VulcanLab"` - verify consistency:
```toml
[project]
name = "VulcanLab"
description = "A Retrieval-Augmented Generation workbench for academic literature"
```

### 3. Database Schema

#### 3.1 Database Names
- **Current DB**: `psych_rag_test`
- **New DB**: `vulcanlab_test`

- **Current User**: `psych_rag_app_user_test`
- **New User**: `vulcanlab_app_user`

#### 3.2 Migration Strategy
Create migration script to:
1. Create new database `vulcanlab_test`
2. Copy schema from `psych_rag_test`
3. Migrate all data
4. Create new user `vulcanlab_app_user` with appropriate permissions
5. Provide rollback capability

**Note**: Table names and column names likely don't need changing (unless they contain "psych_rag" prefix)

### 4. Frontend/UI Application

#### 4.1 Package Rename
- **Current**: `psychrag_ui/`
- **New**: `vulcanlab_ui/`

#### 4.2 package.json
```json
{
  "name": "vulcanlab_ui",  // was: psychrag_ui
  "version": "0.1.0",
  "private": true,
  ...
}
```

#### 4.3 UI Text Content
Update all user-facing text:
- Page titles
- Headers
- Navigation labels
- Error messages
- Help text

**Key Files to Check:**
- `psychrag_ui/src/app/**/*.tsx`
- `psychrag_ui/src/components/**/*.tsx`

#### 4.4 API Endpoint URLs
Update API base URLs if they contain "psychrag":
```typescript
// Before
const API_BASE = 'http://localhost:8000/psychrag/api'

// After
const API_BASE = 'http://localhost:8000/vulcanlab/api'
```

### 5. Documentation

#### 5.1 README.md
- Update project title: "PsychRAG" → "VulcanLab"
- Update all command examples
- Update all references to package names
- Update description: "psychology literature" → "academic literature" (if appropriate)

#### 5.2 Documentation Files
Update all `.md` files in `documentation/`:
- Keep historical context where appropriate
- Update current instructions and examples
- Update file paths and references

#### 5.3 Code Comments
Update docstrings and comments that mention "PsychRAG"

### 6. File System Paths

#### 6.1 Data Directories
Users may need to update their data directory paths:
- **Old**: `D:\psychRAG_data\`
- **New**: `D:\vulcanlab_data\`

**Recommendation**: Provide migration script or clear instructions

#### 6.2 Output Directories
Update any hardcoded paths in code that reference "psychRAG"

### 7. Testing Requirements

#### 7.1 Test Files
Update all test files in `tests/`:
- Import statements
- Test data references
- Mock configurations

#### 7.2 Test Coverage
Ensure all renamed modules are tested:
- Unit tests pass
- Integration tests pass
- API endpoints work
- UI loads correctly

#### 7.3 Migration Testing
Test database migration:
- Data integrity preserved
- All queries work with new schema
- Rollback works correctly

### 8. Git and Repository

#### 8.1 Repository Name
Consider renaming repository:
- **Current**: `psychRAG-test`
- **New**: `vulcanlab-test` or `vulcanlab`

#### 8.2 .gitignore
Update if it contains "psychrag" specific patterns

#### 8.3 Workspace Files
- Update `.code-workspace` files
- Update any IDE-specific config

### 9. API Routes

#### 9.1 FastAPI Router Prefixes
Check and update router prefixes in `src/psychrag_api/`:
```python
# Check if routers use psychrag in paths
router = APIRouter(prefix="/api/psychrag")  # Update if exists
```

#### 9.2 API Documentation
FastAPI auto-generates docs - ensure they show "VulcanLab" after rename

### 10. Dependencies and Requirements

#### 10.1 Package Dependencies
Review if any dependencies reference the package name:
- Check `pyproject.toml` dependencies
- Check `package.json` dependencies

#### 10.2 Virtual Environment
Developers will need to:
1. Recreate virtual environment
2. Reinstall with `pip install -e .`

## Implementation Plan

### Phase 1: Preparation (T001)
1. Create backup of entire codebase
2. Create backup of database
3. Document all "psychrag" occurrences
4. Create rollback plan

### Phase 2: Core Python Package (T002)
1. Rename `src/psychrag/` → `src/vulcanlab/`
2. Update all import statements in core package
3. Update `__init__.py` files
4. Run tests

### Phase 3: API Package (T003)
1. Rename `src/psychrag_api/` → `src/vulcanlab_api/`
2. Update all import statements
3. Update router configurations
4. Test API endpoints

### Phase 4: Frontend (T004)
1. Rename `psychrag_ui/` → `vulcanlab_ui/`
2. Update package.json
3. Update all UI text and references
4. Update API calls
5. Test UI functionality

### Phase 5: Configuration & Database (T005)
1. Rename `psychrag.config.json` → `vulcanlab.config.json`
2. Update configuration loader code
3. Create database migration script
4. Test migration with dev database
5. Update environment variable documentation

### Phase 6: Documentation (T006)
1. Update README.md
2. Update all documentation in `documentation/`
3. Update code comments and docstrings
4. Update CLI help text

### Phase 7: Testing & Verification (T007)
1. Run full test suite
2. Manual testing of all features
3. Verify database migration
4. Verify configuration loading
5. Verify UI loads and functions
6. Check all CLI commands

### Phase 8: Final Cleanup (T008)
1. Update Git repository metadata
2. Search for any missed references
3. Update project-specific files (workspace, etc.)
4. Create migration guide for users

## Success Criteria

- [ ] All 838+ occurrences of "psychrag"/"PsychRAG" updated appropriately
- [ ] All Python imports work correctly
- [ ] All tests pass
- [ ] UI loads and functions correctly
- [ ] API endpoints respond correctly
- [ ] Database migration works
- [ ] Configuration system loads new config file
- [ ] Documentation is complete and accurate
- [ ] CLI commands work with new module names
- [ ] No broken references or imports

## Risks and Mitigation

### Risk 1: Broken Imports
**Mitigation**: Comprehensive testing, use IDE refactoring tools, grep verification

### Risk 2: Database Migration Failure
**Mitigation**: Full backup, test on dev environment first, rollback script ready

### Risk 3: User Disruption
**Mitigation**: Clear migration guide, version documentation, support for old paths

### Risk 4: Missed References
**Mitigation**: Multiple grep passes with different patterns, manual code review

### Risk 5: External Dependencies
**Mitigation**: Check if any external systems reference "psychrag" by name

## Post-Rename Tasks

1. **User Communication**: Notify users of rename and provide migration instructions
2. **Update Deployment**: Update any deployment scripts or CI/CD pipelines
3. **Archive Old Docs**: Keep old documentation for reference if needed
4. **Monitor Issues**: Watch for any issues related to the rename in first few weeks
5. **Update Package Repository**: If published, update package metadata

## Open Questions

1. Should we maintain `psychrag` as a deprecated alias for backward compatibility?
2. Do any external systems or APIs reference the "psychrag" name?
3. Are there any published packages or documentation that reference the old name?
4. Should the database table names be renamed or only the database/user names?
5. What is the timeline for this rename?

## Notes

- The pyproject.toml already shows "VulcanLab" as the package name, suggesting partial rename may have started
- Some documentation files already reference VulcanLab
- Existing file `documentation/rename-to-vulcanlab.md` may contain additional context (19 occurrences)
- Existing file `documentation/rename-to-vulcanlab-checklist.md` may be outdated or need updating
