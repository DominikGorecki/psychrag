COMPLETE

# T02: Backend models and config loader utility

## Context

- **PRD**: [prd-rag-settings.md](prd-rag-settings.md)
- **PRD Sections**: Technical Specification → Database Model (lines 146-171) and Config Loader Utility (lines 252-296)
- **User value**: Provides Python-level access to RAG configurations, enabling the backend to load and use preset parameters without raw SQL queries.

## Outcome

When this ticket is done:
- SQLAlchemy model `RagConfig` exists and maps to the `rag_config` table
- Utility module `rag_config_loader.py` provides clean API for loading configs by name or default
- Python code can import and use: `get_default_config()` and `get_config_by_name(preset_name)`
- All functions handle errors gracefully with clear exceptions

## Scope

### In scope:
- Create SQLAlchemy model `src/psychrag/data/models/rag_config.py`
- Create utility module `src/psychrag/utils/rag_config_loader.py` with:
  - `get_default_config()` - returns default preset's config dict
  - `get_config_by_name(preset_name)` - returns specific preset's config dict
- Update `src/psychrag/data/models/__init__.py` to export `RagConfig`
- Unit tests for model and utility functions

### Out of scope:
- API endpoints (T03)
- Integration into retrieval/consolidation/augmentation modules (T04)
- Frontend UI (T05)
- Validation logic (handled in T03's Pydantic schemas)

## Implementation plan

### Backend - SQLAlchemy Model

**File**: `src/psychrag/data/models/rag_config.py`

1. **Create model class** following existing model patterns (reference `query.py`, `prompt_template.py`):

```python
"""
RAG configuration model for storing preset parameters.

This module defines the RagConfig model for storing and managing
RAG pipeline configuration presets (retrieval, consolidation, augmentation).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class RagConfig(Base):
    """
    Model representing a RAG configuration preset.

    Each preset contains parameters for retrieval, consolidation, and
    augmentation stages of the RAG pipeline.

    Attributes:
        id: Primary key.
        preset_name: Unique human-readable name for the preset.
        is_default: Whether this preset is the system default (only one can be true).
        description: Optional description of preset purpose and use cases.
        config: JSONB containing retrieval, consolidation, and augmentation parameters.
        created_at: Timestamp when preset was created.
        updated_at: Timestamp when preset was last updated (auto-updated by trigger).
    """

    __tablename__ = "rag_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    preset_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )

    def __repr__(self) -> str:
        """String representation of RagConfig."""
        default_marker = " (default)" if self.is_default else ""
        return f"<RagConfig(id={self.id}, preset_name='{self.preset_name}'{default_marker})>"
```

2. **Update model exports** in `src/psychrag/data/models/__init__.py`:

```python
# Add to existing imports
from .rag_config import RagConfig

# Add to __all__ list
__all__ = [
    "Chunk",
    "Query",
    "Result",
    "Work",
    "IOFile",
    "PromptTemplate",
    "PromptMeta",
    "RagConfig",  # Add this
]
```

### Backend - Config Loader Utility

**File**: `src/psychrag/utils/rag_config_loader.py`

1. **Create utility module** with two main functions:

```python
"""
RAG configuration loader utility.

Provides functions to load RAG configuration presets from the database.
Used by retrieval, consolidation, and augmentation modules to get
runtime parameters.

Example:
    >>> from psychrag.utils.rag_config_loader import get_default_config
    >>> config = get_default_config()
    >>> dense_limit = config["retrieval"]["dense_limit"]
"""

from typing import Optional

from sqlalchemy.orm import Session

from psychrag.data.database import get_session
from psychrag.data.models.rag_config import RagConfig


def get_default_config() -> dict:
    """
    Get default RAG configuration from database.

    Returns the configuration dict for the preset marked as default.
    This is the primary function used by RAG pipeline modules.

    Returns:
        Dict with keys: "retrieval", "consolidation", "augmentation".
        Each key contains a dict of parameters for that stage.

    Raises:
        RuntimeError: If no default configuration exists in database.

    Example:
        >>> config = get_default_config()
        >>> config["retrieval"]["dense_limit"]
        19
        >>> config["consolidation"]["coverage_threshold"]
        0.5
    """
    with get_session() as session:
        config = session.query(RagConfig).filter(RagConfig.is_default == True).first()
        if not config:
            raise RuntimeError(
                "No default RAG configuration found in database. "
                "Run database initialization to create default preset."
            )
        return config.config


def get_config_by_name(preset_name: str) -> dict:
    """
    Get RAG configuration by preset name.

    Loads a specific preset by name. Use this when you want to override
    the default configuration for a specific query or experiment.

    Args:
        preset_name: Name of the preset to load (case-sensitive).

    Returns:
        Dict with keys: "retrieval", "consolidation", "augmentation".
        Each key contains a dict of parameters for that stage.

    Raises:
        ValueError: If preset with given name not found.

    Example:
        >>> config = get_config_by_name("Fast")
        >>> config["retrieval"]["top_n_final"]
        10
    """
    with get_session() as session:
        config = session.query(RagConfig).filter(RagConfig.preset_name == preset_name).first()
        if not config:
            raise ValueError(
                f"RAG config preset '{preset_name}' not found. "
                f"Use get_default_config() or verify preset name."
            )
        return config.config


def get_all_preset_names() -> list[str]:
    """
    Get list of all available preset names.

    Useful for CLI tools, logging, or UI dropdown population.

    Returns:
        List of preset names sorted alphabetically.

    Example:
        >>> get_all_preset_names()
        ['Default', 'Fast', 'Thorough']
    """
    with get_session() as session:
        presets = session.query(RagConfig.preset_name).order_by(RagConfig.preset_name).all()
        return [preset[0] for preset in presets]
```

2. **Consider adding cache** (optional enhancement, not blocking):

If performance becomes an issue, add simple caching:

```python
from functools import lru_cache

@lru_cache(maxsize=32)
def _get_config_cached(preset_name: Optional[str] = None) -> dict:
    """Internal cached version. Cache expires on process restart."""
    if preset_name:
        return get_config_by_name(preset_name)
    return get_default_config()
```

## Unit tests

**File**: `tests/unit/test_rag_config_loader.py`

Create comprehensive tests for the loader utility:

```python
"""
Unit tests for RAG config loader utility.

Tests config loading, error handling, and edge cases.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from psychrag.data.database import get_session
from psychrag.data.models.rag_config import RagConfig
from psychrag.utils.rag_config_loader import (
    get_default_config,
    get_config_by_name,
    get_all_preset_names,
)


class TestGetDefaultConfig:
    """Tests for get_default_config function."""

    def test_get_default_config_success(self):
        """Test successful retrieval of default config."""
        config = get_default_config()

        # Verify structure
        assert isinstance(config, dict)
        assert "retrieval" in config
        assert "consolidation" in config
        assert "augmentation" in config

    def test_get_default_config_has_required_params(self):
        """Test that default config has all required parameters."""
        config = get_default_config()

        # Check retrieval params (sample)
        assert "dense_limit" in config["retrieval"]
        assert "lexical_limit" in config["retrieval"]
        assert "mmr_lambda" in config["retrieval"]

        # Check consolidation params
        assert "coverage_threshold" in config["consolidation"]
        assert "line_gap" in config["consolidation"]

        # Check augmentation params
        assert "top_n_contexts" in config["augmentation"]

    def test_get_default_config_returns_copy(self):
        """Test that returned config is independent (not shared reference)."""
        config1 = get_default_config()
        config2 = get_default_config()

        # Modify one
        config1["retrieval"]["dense_limit"] = 999

        # Verify other is unchanged (if not using cache)
        # This test may need adjustment if caching is implemented
        assert config2["retrieval"]["dense_limit"] != 999

    def test_get_default_config_no_default_raises(self):
        """Test that RuntimeError is raised when no default exists."""
        # Remove default preset
        with get_session() as session:
            session.query(RagConfig).filter(RagConfig.is_default == True).delete()
            session.commit()

        with pytest.raises(RuntimeError, match="No default RAG configuration found"):
            get_default_config()

        # Cleanup: restore default for other tests
        from psychrag.data.init_db import create_default_rag_config
        create_default_rag_config()


class TestGetConfigByName:
    """Tests for get_config_by_name function."""

    @pytest.fixture(autouse=True)
    def setup_test_preset(self):
        """Create a test preset for these tests."""
        with get_session() as session:
            # Check if already exists
            existing = session.query(RagConfig).filter(
                RagConfig.preset_name == "TestPreset"
            ).first()

            if not existing:
                test_preset = RagConfig(
                    preset_name="TestPreset",
                    is_default=False,
                    description="Test preset for unit tests",
                    config={
                        "retrieval": {"dense_limit": 10},
                        "consolidation": {"line_gap": 5},
                        "augmentation": {"top_n_contexts": 3}
                    }
                )
                session.add(test_preset)
                session.commit()

        yield

        # Cleanup
        with get_session() as session:
            session.query(RagConfig).filter(
                RagConfig.preset_name == "TestPreset"
            ).delete()
            session.commit()

    def test_get_config_by_name_success(self):
        """Test successful retrieval by preset name."""
        config = get_config_by_name("TestPreset")

        assert isinstance(config, dict)
        assert config["retrieval"]["dense_limit"] == 10
        assert config["consolidation"]["line_gap"] == 5
        assert config["augmentation"]["top_n_contexts"] == 3

    def test_get_config_by_name_not_found_raises(self):
        """Test that ValueError is raised for non-existent preset."""
        with pytest.raises(ValueError, match="RAG config preset 'NonExistent' not found"):
            get_config_by_name("NonExistent")

    def test_get_config_by_name_case_sensitive(self):
        """Test that preset name lookup is case-sensitive."""
        # Should work with exact case
        config = get_config_by_name("TestPreset")
        assert config is not None

        # Should fail with different case
        with pytest.raises(ValueError):
            get_config_by_name("testpreset")


class TestGetAllPresetNames:
    """Tests for get_all_preset_names function."""

    def test_get_all_preset_names_returns_list(self):
        """Test that function returns a list of strings."""
        names = get_all_preset_names()

        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(name, str) for name in names)

    def test_get_all_preset_names_includes_default(self):
        """Test that default preset is included."""
        names = get_all_preset_names()
        assert "Default" in names

    def test_get_all_preset_names_sorted(self):
        """Test that preset names are returned in alphabetical order."""
        # Create presets with different names
        with get_session() as session:
            for name in ["Zebra", "Alpha", "Middle"]:
                existing = session.query(RagConfig).filter(
                    RagConfig.preset_name == name
                ).first()
                if not existing:
                    preset = RagConfig(
                        preset_name=name,
                        is_default=False,
                        config={"retrieval": {}, "consolidation": {}, "augmentation": {}}
                    )
                    session.add(preset)
            session.commit()

        names = get_all_preset_names()
        sorted_names = sorted(names)
        assert names == sorted_names

        # Cleanup
        with get_session() as session:
            session.query(RagConfig).filter(
                RagConfig.preset_name.in_(["Zebra", "Alpha", "Middle"])
            ).delete()
            session.commit()


class TestRagConfigModel:
    """Tests for RagConfig SQLAlchemy model."""

    def test_model_create_and_retrieve(self):
        """Test creating and retrieving a RagConfig instance."""
        with get_session() as session:
            config = RagConfig(
                preset_name="ModelTest",
                is_default=False,
                description="Test description",
                config={
                    "retrieval": {"dense_limit": 20},
                    "consolidation": {"line_gap": 10},
                    "augmentation": {"top_n_contexts": 7}
                }
            )
            session.add(config)
            session.commit()
            config_id = config.id

        # Retrieve
        with get_session() as session:
            retrieved = session.query(RagConfig).filter(RagConfig.id == config_id).first()
            assert retrieved is not None
            assert retrieved.preset_name == "ModelTest"
            assert retrieved.is_default is False
            assert retrieved.config["retrieval"]["dense_limit"] == 20

        # Cleanup
        with get_session() as session:
            session.query(RagConfig).filter(RagConfig.id == config_id).delete()
            session.commit()

    def test_model_repr(self):
        """Test __repr__ method."""
        with get_session() as session:
            default = session.query(RagConfig).filter(RagConfig.is_default == True).first()
            repr_str = repr(default)

            assert "RagConfig" in repr_str
            assert "Default" in repr_str
            assert "(default)" in repr_str

    def test_model_jsonb_query(self):
        """Test querying JSONB fields."""
        with get_session() as session:
            # Query for configs with dense_limit > 15
            from sqlalchemy import cast, Integer
            results = session.query(RagConfig).filter(
                cast(RagConfig.config["retrieval"]["dense_limit"], Integer) > 15
            ).all()

            assert len(results) > 0
```

**Test execution**:
```bash
venv\Scripts\pytest tests/unit/test_rag_config_loader.py -v
```

**Coverage expectations**:
- Model: creation, retrieval, repr
- get_default_config: success, error when no default
- get_config_by_name: success, error when not found, case sensitivity
- get_all_preset_names: returns list, sorted order
- JSONB querying capabilities

## Dependencies and sequencing

### Dependencies:
- **Requires**: T01 (database schema and migration must be complete)
- **Blocks**: T03 (API needs model), T04 (integration needs loader utility)

### Sequencing notes:
- Can start immediately after T01 is complete
- T03 and T04 can both begin as soon as T02 is done
- This ticket is small and should be quick to complete (~half day)

## Clarifications and assumptions

### Assumptions:
1. **Return type**: Functions return `dict` (not Pydantic models) for flexibility
2. **Session management**: Using `get_session()` context manager from existing database module
3. **Error handling**: Using standard Python exceptions (`RuntimeError`, `ValueError`)
4. **Caching**: Not implementing initially, but structure allows adding `@lru_cache` later
5. **Config dict structure**: Returned dict matches JSONB structure exactly (no transformation)

### Open questions (non-blocking):
1. Should we add validation of config structure in the loader? (PRD suggests validation in API layer)
2. Should `get_config_by_name()` fall back to default if name not found? (Current: raise error)
3. Should we add logging for config loads? (Useful for debugging but adds dependency)

### Implementer notes:

> **Before implementing**:
> - Review existing models (`query.py`, `prompt_template.py`) to match coding style
> - Ensure T01 database migration has been run successfully
> - Review `database.py` to understand `get_session()` usage pattern

> **During implementation**:
> - Keep utility functions simple - no complex logic or transformations
> - Use descriptive error messages that guide users to solutions
> - Follow existing naming conventions for consistency

> **After implementation**:
> - Run all unit tests and verify 100% pass
> - Test import in Python REPL: `from psychrag.utils.rag_config_loader import get_default_config`
> - Verify model appears in SQLAlchemy metadata: `RagConfig.__table__`
> - Test that `get_default_config()` returns expected structure
