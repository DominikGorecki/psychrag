COMPLETE

# T01: Database schema and migration for RAG config

## Context

- **PRD**: [prd-rag-settings.md](prd-rag-settings.md)
- **PRD Sections**: Technical Specification → Database Schema (lines 31-93)
- **User value**: Establishes the foundational database structure for storing RAG configuration presets, enabling users to persist and manage different parameter sets for retrieval, consolidation, and augmentation.

## Outcome

When this ticket is done:
- The `rag_config` table exists in PostgreSQL with proper schema, indexes, and constraints
- Database triggers ensure data integrity (single default preset, auto-update timestamps)
- A default "Default" preset is seeded with balanced RAG parameters
- Both migration SQL and init_db.py support clean installs and existing databases

## Scope

### In scope:
- Create migration file `migrations/013_create_rag_config.sql` with:
  - Table definition with JSONB config column
  - Indexes on `preset_name` and `is_default`
  - Trigger for auto-updating `updated_at` timestamp
  - Trigger to enforce single default preset constraint
  - Default preset insertion
  - Column comments for documentation
- Update `src/psychrag/data/init_db.py` to seed default preset if none exists (idempotent)
- Manual testing: verify migration runs, triggers work, constraints enforced

### Out of scope:
- SQLAlchemy model creation (T02)
- API endpoints (T03)
- Frontend UI (T05)

## Implementation plan

### Backend - Migration SQL

**File**: `migrations/013_create_rag_config.sql`

1. **Table creation**:
   ```sql
   CREATE TABLE IF NOT EXISTS rag_config (
       id SERIAL PRIMARY KEY,
       preset_name VARCHAR(100) UNIQUE NOT NULL,
       is_default BOOLEAN NOT NULL DEFAULT FALSE,
       description TEXT,
       config JSONB NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

2. **Indexes**:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_rag_config_preset_name ON rag_config(preset_name);
   CREATE INDEX IF NOT EXISTS idx_rag_config_is_default ON rag_config(is_default) WHERE is_default = TRUE;
   ```

3. **Trigger for updated_at**:
   ```sql
   CREATE OR REPLACE FUNCTION update_rag_config_updated_at()
   RETURNS TRIGGER AS $$
   BEGIN
       NEW.updated_at = CURRENT_TIMESTAMP;
       RETURN NEW;
   END;
   $$ LANGUAGE plpgsql;

   CREATE TRIGGER trigger_update_rag_config_updated_at
       BEFORE UPDATE ON rag_config
       FOR EACH ROW
       EXECUTE FUNCTION update_rag_config_updated_at();
   ```

4. **Trigger to enforce single default**:
   ```sql
   CREATE OR REPLACE FUNCTION ensure_single_default_rag_config()
   RETURNS TRIGGER AS $$
   BEGIN
       IF NEW.is_default = TRUE THEN
           UPDATE rag_config SET is_default = FALSE WHERE id != NEW.id;
       END IF;
       RETURN NEW;
   END;
   $$ LANGUAGE plpgsql;

   CREATE TRIGGER trigger_ensure_single_default_rag_config
       AFTER INSERT OR UPDATE ON rag_config
       FOR EACH ROW
       WHEN (NEW.is_default = TRUE)
       EXECUTE FUNCTION ensure_single_default_rag_config();
   ```

5. **Insert default preset** (use JSONB structure from PRD lines 49-77):
   ```sql
   INSERT INTO rag_config (preset_name, is_default, description, config)
   VALUES (
       'Default',
       TRUE,
       'Default RAG configuration with balanced settings for general-purpose queries',
       '{
           "retrieval": {
               "dense_limit": 19,
               "lexical_limit": 5,
               "rrf_k": 50,
               "top_k_rrf": 75,
               "top_n_final": 17,
               "entity_boost": 0.05,
               "min_word_count": 150,
               "min_char_count": 250,
               "min_content_length": 750,
               "enrich_lines_above": 0,
               "enrich_lines_below": 13,
               "mmr_lambda": 0.7,
               "reranker_batch_size": 8,
               "reranker_max_length": 512
           },
           "consolidation": {
               "coverage_threshold": 0.5,
               "line_gap": 7,
               "min_content_length": 350,
               "enrich_from_md": true
           },
           "augmentation": {
               "top_n_contexts": 5
           }
       }'::JSONB
   )
   ON CONFLICT (preset_name) DO NOTHING;
   ```

6. **Add comments** for documentation:
   ```sql
   COMMENT ON TABLE rag_config IS 'RAG configuration presets for retrieval, consolidation, and augmentation parameters';
   COMMENT ON COLUMN rag_config.preset_name IS 'Unique human-readable name for the preset';
   COMMENT ON COLUMN rag_config.is_default IS 'Whether this preset is the default (only one can be true)';
   COMMENT ON COLUMN rag_config.config IS 'JSONB configuration with retrieval, consolidation, and augmentation sections';
   ```

### Backend - Python initialization

**File**: `src/psychrag/data/init_db.py`

1. **Add import** (after existing model imports around line 30):
   ```python
   from .models.rag_config import RagConfig  # noqa: F401
   ```

2. **Create function** to seed default preset (add after `create_prompt_meta_table` function):
   ```python
   def create_default_rag_config(verbose: bool = False) -> None:
       """
       Create default RAG configuration preset if none exists.

       This function is idempotent - it only creates the preset if the table is empty.

       Args:
           verbose: If True, print progress information.
       """
       from .database import get_session

       with get_session() as session:
           # Check if any presets exist
           existing = session.query(RagConfig).first()
           if existing:
               if verbose:
                   print("RAG config presets already exist, skipping default creation")
               return

           # Create default preset with balanced settings
           default_config = RagConfig(
               preset_name="Default",
               is_default=True,
               description="Default RAG configuration with balanced settings for general-purpose queries",
               config={
                   "retrieval": {
                       "dense_limit": 19,
                       "lexical_limit": 5,
                       "rrf_k": 50,
                       "top_k_rrf": 75,
                       "top_n_final": 17,
                       "entity_boost": 0.05,
                       "min_word_count": 150,
                       "min_char_count": 250,
                       "min_content_length": 750,
                       "enrich_lines_above": 0,
                       "enrich_lines_below": 13,
                       "mmr_lambda": 0.7,
                       "reranker_batch_size": 8,
                       "reranker_max_length": 512
                   },
                   "consolidation": {
                       "coverage_threshold": 0.5,
                       "line_gap": 7,
                       "min_content_length": 350,
                       "enrich_from_md": True
                   },
                   "augmentation": {
                       "top_n_contexts": 5
                   }
               }
           )
           session.add(default_config)
           session.commit()

           if verbose:
               print("Created default RAG config preset")
   ```

3. **Update `init_database()` function** (add call after `create_prompt_meta_table(verbose=verbose)` around line 382):
   ```python
   def init_database(verbose: bool = False) -> None:
       """Initialize the complete database schema and seed data."""
       create_database_and_user(verbose=verbose)
       enable_pgvector_extension(verbose=verbose)
       create_tables(verbose=verbose)
       create_vector_indexes(verbose=verbose)
       create_fulltext_search(verbose=verbose)
       create_prompt_meta_table(verbose=verbose)
       create_default_rag_config(verbose=verbose)  # Add this line
   ```

### Migration execution order

1. Ensure previous migrations (001-012) have been run
2. Run `013_create_rag_config.sql` using psql or your migration tool
3. Verify table exists: `\d rag_config`
4. Verify triggers exist: `\df update_rag_config_updated_at` and `\df ensure_single_default_rag_config`
5. Verify default preset inserted: `SELECT * FROM rag_config;`

## Unit tests

**File**: `tests/unit/test_rag_config_db.py`

Create comprehensive tests for database schema and constraints:

```python
"""
Unit tests for RAG config database schema and constraints.

Tests table structure, triggers, and data integrity.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from psychrag.data.database import engine, get_session
from psychrag.data.models.rag_config import RagConfig


class TestRagConfigSchema:
    """Test rag_config table schema and structure."""

    def test_table_exists(self):
        """Verify rag_config table exists."""
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_name = 'rag_config')"
            ))
            assert result.scalar() is True

    def test_columns_exist(self):
        """Verify all required columns exist with correct types."""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'rag_config'
            """))
            columns = {row[0]: row[1] for row in result}

        assert columns['id'] == 'integer'
        assert columns['preset_name'] == 'character varying'
        assert columns['is_default'] == 'boolean'
        assert columns['description'] == 'text'
        assert columns['config'] == 'jsonb'
        assert columns['created_at'] == 'timestamp without time zone'
        assert columns['updated_at'] == 'timestamp without time zone'

    def test_indexes_exist(self):
        """Verify indexes are created."""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'rag_config'
            """))
            indexes = [row[0] for row in result]

        assert 'idx_rag_config_preset_name' in indexes
        assert 'idx_rag_config_is_default' in indexes

    def test_triggers_exist(self):
        """Verify triggers are created."""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT trigger_name FROM information_schema.triggers
                WHERE event_object_table = 'rag_config'
            """))
            triggers = [row[0] for row in result]

        assert 'trigger_update_rag_config_updated_at' in triggers
        assert 'trigger_ensure_single_default_rag_config' in triggers


class TestRagConfigConstraints:
    """Test database constraints and triggers."""

    def test_preset_name_unique_constraint(self):
        """Test that duplicate preset names are rejected."""
        with get_session() as session:
            # Create first preset
            preset1 = RagConfig(
                preset_name="TestUnique",
                is_default=False,
                config={"retrieval": {}, "consolidation": {}, "augmentation": {}}
            )
            session.add(preset1)
            session.commit()

            # Try to create duplicate
            with pytest.raises(IntegrityError):
                preset2 = RagConfig(
                    preset_name="TestUnique",
                    is_default=False,
                    config={"retrieval": {}, "consolidation": {}, "augmentation": {}}
                )
                session.add(preset2)
                session.commit()

    def test_single_default_trigger(self):
        """Test that only one preset can have is_default=True."""
        with get_session() as session:
            # Create two presets, both marked as default
            preset1 = RagConfig(
                preset_name="Default1",
                is_default=True,
                config={"retrieval": {}, "consolidation": {}, "augmentation": {}}
            )
            preset2 = RagConfig(
                preset_name="Default2",
                is_default=True,
                config={"retrieval": {}, "consolidation": {}, "augmentation": {}}
            )

            session.add(preset1)
            session.commit()

            session.add(preset2)
            session.commit()

            # Query to verify only one is default
            defaults = session.query(RagConfig).filter(RagConfig.is_default == True).all()
            assert len(defaults) == 1
            assert defaults[0].preset_name == "Default2"

    def test_updated_at_trigger(self):
        """Test that updated_at is automatically set on UPDATE."""
        import time

        with get_session() as session:
            # Create preset
            preset = RagConfig(
                preset_name="UpdateTest",
                is_default=False,
                config={"retrieval": {}, "consolidation": {}, "augmentation": {}}
            )
            session.add(preset)
            session.commit()

            original_updated_at = preset.updated_at
            time.sleep(1)

            # Update preset
            preset.description = "Updated description"
            session.commit()

            # Verify updated_at changed
            session.refresh(preset)
            assert preset.updated_at > original_updated_at


class TestDefaultPresetSeed:
    """Test default preset seeding."""

    def test_default_preset_exists(self):
        """Verify default preset was created."""
        with get_session() as session:
            default = session.query(RagConfig).filter(
                RagConfig.preset_name == "Default"
            ).first()

            assert default is not None
            assert default.is_default is True
            assert default.description is not None

    def test_default_preset_has_all_params(self):
        """Verify default preset has all required parameters."""
        with get_session() as session:
            default = session.query(RagConfig).filter(
                RagConfig.preset_name == "Default"
            ).first()

            config = default.config
            assert "retrieval" in config
            assert "consolidation" in config
            assert "augmentation" in config

            # Check retrieval params
            assert "dense_limit" in config["retrieval"]
            assert "lexical_limit" in config["retrieval"]
            assert "rrf_k" in config["retrieval"]
            assert "mmr_lambda" in config["retrieval"]

            # Check consolidation params
            assert "coverage_threshold" in config["consolidation"]
            assert "line_gap" in config["consolidation"]

            # Check augmentation params
            assert "top_n_contexts" in config["augmentation"]
```

**Test execution**:
```bash
venv\Scripts\pytest tests/unit/test_rag_config_db.py -v
```

**Coverage expectations**:
- Table structure: columns, types, indexes
- Constraints: unique preset_name
- Triggers: single default, auto-update timestamp
- Default preset: existence and structure

## Dependencies and sequencing

### Dependencies:
- **Before this ticket**: Migrations 001-012 must be applied
- **After this ticket**: T02 (SQLAlchemy model), T03 (API), T04 (integration)

### Sequencing notes:
- This is the foundation ticket - all other tickets depend on it
- Can be developed and tested independently
- Once complete, T02 and T04 can be developed in parallel
- Migration must be idempotent (safe to re-run)

## Clarifications and assumptions

### Assumptions:
1. **Migration numbering**: Using `013_create_rag_config.sql` as next sequential number
2. **Default values**: Using the exact parameter values from PRD lines 52-76
3. **JSONB structure**: Using nested object structure (not flattened)
4. **Trigger behavior**: Single default constraint updates ALL other rows to false when new default set
5. **Idempotency**: Both migration and init_db use `IF NOT EXISTS` / `ON CONFLICT DO NOTHING` patterns

### Open questions (non-blocking):
1. Should we add a `version` column for future config schema evolution?
2. Should we add audit columns (`created_by`, `updated_by`) for multi-user scenarios?
3. Should the trigger prevent deletion of the default preset?

### Implementer notes:

> **Before implementing**:
> - Review existing migration files (001-012) to match SQL style and conventions
> - Verify PostgreSQL version supports JSONB and all trigger syntax used
> - Ensure test database is available for unit tests
> - Review `init_db.py` structure to match existing function patterns

> **During implementation**:
> - Test trigger behavior thoroughly - single default constraint is critical
> - Verify JSONB query performance with indexes
> - Test migration rollback if your migration tool supports it

> **After implementation**:
> - Run migration on test database first
> - Verify all unit tests pass
> - Document migration in project changelog/migration log
