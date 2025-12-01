# Quick Reference: psychRAG → VulcanLab Migration Checklist

**Quick checklist for the migration process. See `rename-to-vulcanlab.md` for detailed instructions.**

---

## Pre-Migration

- [ ] Create backup branch: `git checkout -b backup/pre-rename`
- [ ] Commit all current work
- [ ] Create migration branch: `git checkout -b feature/rename-to-vulcanlab`
- [ ] Backup database
- [ ] Ensure all tests pass

---

## Phase 1: Directory Renaming

- [ ] `mv src/psychrag src/vulcanlab`
- [ ] `mv src/psychrag_api src/vulcanlab_api`
- [ ] `mv psychrag_ui vulcanlab_ui`
- [ ] `mv psychrag.config.json vulcanlab.config.json`
- [ ] Clean build artifacts: `rm -rf src/psychrag.egg-info/`
- [ ] Commit: `git add -A && git commit -m "Rename directories"`

---

## Phase 2: Python Package Updates

- [ ] Update `pyproject.toml`: `name = "vulcanlab"`
- [ ] Update `src/vulcanlab/__init__.py`
- [ ] Update `src/vulcanlab_api/__init__.py`
- [ ] Find-replace all imports: `from psychrag.` → `from vulcanlab.`
- [ ] Find-replace all imports: `import psychrag.` → `import vulcanlab.`
- [ ] Update module docstrings (search: `psychrag|psychRAG|PsychRAG`)
- [ ] Test: `pip install -e . && python -c "import vulcanlab; import vulcanlab_api"`
- [ ] Commit: `git add -A && git commit -m "Update Python packages"`

---

## Phase 3: Configuration Files

- [ ] Update `vulcanlab.config.json` database names (optional)
- [ ] Find-replace: `psychrag.config.json` → `vulcanlab.config.json`
- [ ] Update `.env` files if needed
- [ ] Commit: `git add -A && git commit -m "Update config files"`

---

## Phase 4: Frontend Updates

- [ ] Update `vulcanlab_ui/package.json`: `"name": "vulcanlab_ui"`
- [ ] Update `layout.tsx`: title and description
- [ ] Update `nav-bar.tsx`: brand name
- [ ] Update `page.tsx`: welcome text
- [ ] Update `settings/page.tsx`: config file references
- [ ] Test: `cd vulcanlab_ui && npm install && npm run build`
- [ ] Commit: `git add -A && git commit -m "Update frontend"`

---

## Phase 5: Database Updates

- [ ] Backup database: `pg_dump -U postgres psych_rag_test > backup.sql`
- [ ] Rename database: `ALTER DATABASE psych_rag_test RENAME TO vulcanlab_test;`
- [ ] Update `vulcanlab.config.json` database name
- [ ] Test connection: `python -c "from vulcanlab.data.database import get_session; get_session()"`
- [ ] Commit: `git add vulcanlab.config.json && git commit -m "Update database config"`

---

## Phase 6: Documentation Updates

- [ ] Update `README.md`: title, commands, references
- [ ] Update `project-structure.md`
- [ ] Update `.cursorrules`
- [ ] Update `.claude/instructions.md`
- [ ] Update `src/vulcanlab_api/README.md`
- [ ] Update all module `README.md` files
- [ ] Update all files in `documentation/` folder
- [ ] Commit: `git add -A && git commit -m "Update documentation"`

---

## Phase 7: Testing & Verification

- [ ] Run tests: `pytest`
- [ ] Test CLI: `python -m vulcanlab.config.app_config_cli show`
- [ ] Test API: `python -m vulcanlab_api` (check http://localhost:8000/docs)
- [ ] Test frontend: `cd vulcanlab_ui && npm run dev`
- [ ] Search for remaining references: `grep -r "psychrag" --exclude-dir=venv --exclude-dir=node_modules .`
- [ ] Fix any issues found
- [ ] Commit fixes

---

## Final Verification

- [ ] Package installs: `pip install -e .`
- [ ] Imports work: `python -c "import vulcanlab; import vulcanlab_api"`
- [ ] CLI works: `python -m vulcanlab.config.app_config_cli show`
- [ ] API works: `python -m vulcanlab_api`
- [ ] Frontend builds: `cd vulcanlab_ui && npm run build`
- [ ] Database connects
- [ ] All tests pass: `pytest`
- [ ] No remaining references found
- [ ] Final commit: `git add -A && git commit -m "Complete migration: psychRAG -> VulcanLab"`

---

## Quick Find-Replace Commands

```bash
# Python imports
find src tests -name "*.py" -exec sed -i 's/from psychrag\./from vulcanlab./g' {} +
find src tests -name "*.py" -exec sed -i 's/import psychrag\./import vulcanlab./g' {} +
find src tests -name "*.py" -exec sed -i 's/psychrag\./vulcanlab./g' {} +

# Documentation
find documentation -name "*.md" -exec sed -i 's/psychRAG/VulcanLab/g' {} +
find documentation -name "*.md" -exec sed -i 's/PsychRAG/VulcanLab/g' {} +
find documentation -name "*.md" -exec sed -i 's/psychrag/vulcanlab/g' {} +

# Config file references
find . -name "*.py" -o -name "*.tsx" -o -name "*.md" | xargs sed -i 's/psychrag\.config\.json/vulcanlab.config.json/g'
```

**Note**: Review all changes before committing. Use version control to track modifications.

---

**See `rename-to-vulcanlab.md` for detailed instructions and troubleshooting.**

