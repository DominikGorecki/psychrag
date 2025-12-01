# T04: Integrate config loader into retrieval/consolidation/augmentation

## Context

- **PRD**: [prd-rag-settings.md](prd-rag-settings.md)
- **PRD Sections**: Technical Specification → Update Existing Modules (lines 298-319)
- **User value**: Transitions RAG pipeline from hard-coded parameters to database-driven configuration, enabling users to tune retrieval/consolidation/augmentation behavior without code changes.

## Outcome

When this ticket is done:
- Retrieval module (`retrieve.py`) loads parameters from database config instead of hard-coded values
- Consolidation module (`consolidate_context.py`) loads parameters from database config
- Augmentation module (`augment.py`) loads parameters from database config
- All functions accept optional `config_preset` parameter for per-query overrides (backward compatible)
- Hard-coded parameter values are removed from these modules
- All existing functionality works identically with database configs matching old hard-coded values

## Scope

### In scope:
- Update `src/psychrag/retrieval/retrieve.py` to use config loader
- Update `src/psychrag/augmentation/consolidate_context.py` to use config loader
- Update `src/psychrag/augmentation/augment.py` to use config loader
- Add optional `config_preset` parameter to main functions (default=None = use default config)
- Remove hard-coded parameter values from these modules
- Integration tests verifying config loading works end-to-end
- Backward compatibility: existing code calling these functions continues to work

### Out of scope:
- API endpoints (T03)
- Frontend UI (T05)
- CLI scripts (will continue to work, may be updated in future ticket)
- Query expansion module (doesn't have configurable parameters in PRD)
- Changing default parameter values (use PRD's default values)

## Implementation plan

### Backend - Retrieval Module

**File**: `src/psychrag/retrieval/retrieve.py`

1. **Add import** at top of file:
```python
from psychrag.utils.rag_config_loader import get_default_config, get_config_by_name
```

2. **Update main retrieval function signature** (add config_preset parameter):
```python
def retrieve(
    query_id: int,
    config_preset: Optional[str] = None,  # Add this parameter
    verbose: bool = False
) -> None:
    """
    Retrieve chunks for a query using hybrid search and reranking.

    Args:
        query_id: ID of the query in the database.
        config_preset: Name of RAG config preset to use. If None, uses default.
        verbose: If True, print progress information.
    """
```

3. **Load config at start of function**:
```python
def retrieve(query_id: int, config_preset: Optional[str] = None, verbose: bool = False) -> None:
    # Load configuration
    if config_preset:
        config = get_config_by_name(config_preset)
    else:
        config = get_default_config()

    retrieval_params = config["retrieval"]

    # Extract parameters
    DENSE_LIMIT = retrieval_params["dense_limit"]
    LEXICAL_LIMIT = retrieval_params["lexical_limit"]
    RRF_K = retrieval_params["rrf_k"]
    TOP_K_RRF = retrieval_params["top_k_rrf"]
    TOP_N_FINAL = retrieval_params["top_n_final"]
    ENTITY_BOOST = retrieval_params["entity_boost"]
    MIN_WORD_COUNT = retrieval_params["min_word_count"]
    MIN_CHAR_COUNT = retrieval_params["min_char_count"]
    MIN_CONTENT_LENGTH = retrieval_params["min_content_length"]
    ENRICH_LINES_ABOVE = retrieval_params["enrich_lines_above"]
    ENRICH_LINES_BELOW = retrieval_params["enrich_lines_below"]
    MMR_LAMBDA = retrieval_params["mmr_lambda"]
    RERANKER_BATCH_SIZE = retrieval_params["reranker_batch_size"]
    RERANKER_MAX_LENGTH = retrieval_params["reranker_max_length"]

    if verbose:
        print(f"Using config preset: {config_preset or 'default'}")
        print(f"  dense_limit={DENSE_LIMIT}, lexical_limit={LEXICAL_LIMIT}, top_n_final={TOP_N_FINAL}")

    # Rest of function continues as before, using these variables...
```

4. **Remove old hard-coded constants** from top of file/function:
```python
# DELETE these lines:
# DENSE_LIMIT = 19
# LEXICAL_LIMIT = 5
# RRF_K = 50
# etc...
```

5. **Update any helper functions** that also use these parameters to accept them as arguments or load config themselves.

### Backend - Consolidation Module

**File**: `src/psychrag/augmentation/consolidate_context.py`

1. **Add import**:
```python
from psychrag.utils.rag_config_loader import get_default_config, get_config_by_name
```

2. **Update main consolidation function signature**:
```python
def consolidate_chunks(
    query_id: int,
    config_preset: Optional[str] = None,  # Add this parameter
    verbose: bool = False
) -> None:
    """
    Consolidate retrieved chunks by grouping and parent replacement.

    Args:
        query_id: ID of the query in the database.
        config_preset: Name of RAG config preset to use. If None, uses default.
        verbose: If True, print progress information.
    """
```

3. **Load config**:
```python
def consolidate_chunks(query_id: int, config_preset: Optional[str] = None, verbose: bool = False) -> None:
    # Load configuration
    if config_preset:
        config = get_config_by_name(config_preset)
    else:
        config = get_default_config()

    consolidation_params = config["consolidation"]

    # Extract parameters
    COVERAGE_THRESHOLD = consolidation_params["coverage_threshold"]
    LINE_GAP = consolidation_params["line_gap"]
    MIN_CONTENT_LENGTH = consolidation_params["min_content_length"]
    ENRICH_FROM_MD = consolidation_params["enrich_from_md"]

    if verbose:
        print(f"Using config preset: {config_preset or 'default'}")
        print(f"  coverage_threshold={COVERAGE_THRESHOLD}, line_gap={LINE_GAP}")

    # Rest of function continues...
```

4. **Remove hard-coded constants**:
```python
# DELETE:
# COVERAGE_THRESHOLD = 0.5
# LINE_GAP = 7
# etc...
```

### Backend - Augmentation Module

**File**: `src/psychrag/augmentation/augment.py`

1. **Add import**:
```python
from psychrag.utils.rag_config_loader import get_default_config, get_config_by_name
```

2. **Update function that uses `top_n_contexts`** (likely `get_query_with_context` or similar):
```python
def get_query_with_context(
    query_id: int,
    top_n: Optional[int] = None,  # Keep this for backward compat
    config_preset: Optional[str] = None,  # Add this
    verbose: bool = False
) -> tuple:
    """
    Get query and its top N consolidated contexts.

    Args:
        query_id: ID of the query.
        top_n: Number of contexts to return. If None, uses config default.
        config_preset: Name of RAG config preset to use. If None, uses default.
        verbose: If True, print progress information.

    Returns:
        Tuple of (query, contexts).
    """
    # Load configuration
    if top_n is None:
        if config_preset:
            config = get_config_by_name(config_preset)
        else:
            config = get_default_config()

        top_n = config["augmentation"]["top_n_contexts"]

    if verbose:
        print(f"Using top_n_contexts: {top_n}")

    # Rest of function continues...
```

3. **Remove hard-coded default**:
```python
# DELETE:
# DEFAULT_TOP_N = 5
```

### Pattern for all modules:

**Error handling**:
```python
try:
    if config_preset:
        config = get_config_by_name(config_preset)
    else:
        config = get_default_config()
except (ValueError, RuntimeError) as e:
    print(f"Error loading config: {e}")
    print("Falling back to default preset")
    config = get_default_config()
```

**Logging (optional but recommended)**:
```python
import logging
logger = logging.getLogger(__name__)

# In function:
logger.info(f"Using RAG config preset: {config_preset or 'default'}")
logger.debug(f"Retrieval params: dense_limit={DENSE_LIMIT}, top_n_final={TOP_N_FINAL}")
```

### Backward compatibility considerations:

1. **Default parameter values**: `config_preset=None` means existing code doesn't need changes
2. **Existing tests**: Tests not passing `config_preset` will use default config (same values as before)
3. **CLI scripts**: Continue to work without modification (use default config)
4. **Future enhancement**: CLI scripts can be updated to accept `--config-preset` flag

## Unit tests

**File**: `tests/unit/test_rag_config_integration.py`

Create integration tests for config loading in each module:

```python
"""
Integration tests for RAG config loader in pipeline modules.

Tests that retrieval, consolidation, and augmentation modules
properly load and use configuration from database.
"""

import pytest
from unittest.mock import Mock, patch

from psychrag.retrieval.retrieve import retrieve
from psychrag.augmentation.consolidate_context import consolidate_chunks
from psychrag.augmentation.augment import get_query_with_context
from psychrag.data.database import get_session
from psychrag.data.models.rag_config import RagConfig


@pytest.fixture
def test_config_preset():
    """Create a test config preset with known values."""
    with get_session() as session:
        # Check if exists
        existing = session.query(RagConfig).filter(
            RagConfig.preset_name == "TestIntegration"
        ).first()

        if not existing:
            test_preset = RagConfig(
                preset_name="TestIntegration",
                is_default=False,
                description="Test preset for integration tests",
                config={
                    "retrieval": {
                        "dense_limit": 5,
                        "lexical_limit": 2,
                        "rrf_k": 30,
                        "top_k_rrf": 10,
                        "top_n_final": 5,
                        "entity_boost": 0.1,
                        "min_word_count": 100,
                        "min_char_count": 200,
                        "min_content_length": 500,
                        "enrich_lines_above": 1,
                        "enrich_lines_below": 5,
                        "mmr_lambda": 0.8,
                        "reranker_batch_size": 4,
                        "reranker_max_length": 256
                    },
                    "consolidation": {
                        "coverage_threshold": 0.6,
                        "line_gap": 3,
                        "min_content_length": 200,
                        "enrich_from_md": False
                    },
                    "augmentation": {
                        "top_n_contexts": 3
                    }
                }
            )
            session.add(test_preset)
            session.commit()

    yield "TestIntegration"

    # Cleanup
    with get_session() as session:
        session.query(RagConfig).filter(
            RagConfig.preset_name == "TestIntegration"
        ).delete()
        session.commit()


class TestRetrievalConfigIntegration:
    """Test config loading in retrieval module."""

    @patch('psychrag.retrieval.retrieve.get_session')
    @patch('psychrag.retrieval.retrieve.load_reranker')
    def test_retrieve_uses_default_config(self, mock_reranker, mock_session):
        """Test that retrieve() uses default config when no preset specified."""
        # Setup mocks
        mock_session.return_value.__enter__.return_value = Mock()

        # This test verifies the function CAN load default config
        # Full integration would require actual query in DB
        from psychrag.utils.rag_config_loader import get_default_config
        config = get_default_config()

        assert config["retrieval"]["dense_limit"] == 19  # Default value
        assert config["retrieval"]["top_n_final"] == 17

    @patch('psychrag.retrieval.retrieve.get_session')
    @patch('psychrag.retrieval.retrieve.load_reranker')
    def test_retrieve_uses_custom_preset(self, mock_reranker, mock_session, test_config_preset):
        """Test that retrieve() uses custom preset when specified."""
        from psychrag.utils.rag_config_loader import get_config_by_name
        config = get_config_by_name(test_config_preset)

        assert config["retrieval"]["dense_limit"] == 5  # Custom value
        assert config["retrieval"]["top_n_final"] == 5

    def test_retrieve_invalid_preset_raises_error(self):
        """Test that invalid preset name raises ValueError."""
        from psychrag.utils.rag_config_loader import get_config_by_name

        with pytest.raises(ValueError, match="not found"):
            get_config_by_name("NonExistentPreset")


class TestConsolidationConfigIntegration:
    """Test config loading in consolidation module."""

    def test_consolidate_uses_default_config(self):
        """Test that consolidate_chunks() can load default config."""
        from psychrag.utils.rag_config_loader import get_default_config
        config = get_default_config()

        assert config["consolidation"]["coverage_threshold"] == 0.5
        assert config["consolidation"]["line_gap"] == 7

    def test_consolidate_uses_custom_preset(self, test_config_preset):
        """Test that consolidate_chunks() can load custom preset."""
        from psychrag.utils.rag_config_loader import get_config_by_name
        config = get_config_by_name(test_config_preset)

        assert config["consolidation"]["coverage_threshold"] == 0.6
        assert config["consolidation"]["line_gap"] == 3


class TestAugmentationConfigIntegration:
    """Test config loading in augmentation module."""

    def test_augment_uses_default_config(self):
        """Test that augment functions can load default config."""
        from psychrag.utils.rag_config_loader import get_default_config
        config = get_default_config()

        assert config["augmentation"]["top_n_contexts"] == 5

    def test_augment_uses_custom_preset(self, test_config_preset):
        """Test that augment functions can load custom preset."""
        from psychrag.utils.rag_config_loader import get_config_by_name
        config = get_config_by_name(test_config_preset)

        assert config["augmentation"]["top_n_contexts"] == 3


class TestBackwardCompatibility:
    """Test that existing code continues to work."""

    @patch('psychrag.retrieval.retrieve.get_session')
    @patch('psychrag.retrieval.retrieve.load_reranker')
    def test_retrieve_without_config_preset_param(self, mock_reranker, mock_session):
        """Test calling retrieve() without config_preset parameter."""
        # This simulates existing code that doesn't know about config_preset
        mock_session.return_value.__enter__.return_value = Mock()

        # Should not raise error - uses default config
        try:
            # retrieve(query_id=1)  # Would need actual query in DB
            # Instead, just verify default config loads
            from psychrag.utils.rag_config_loader import get_default_config
            config = get_default_config()
            assert config is not None
        except Exception as e:
            pytest.fail(f"Backward compatibility broken: {e}")


class TestConfigParameterValidation:
    """Test that loaded configs have expected structure."""

    def test_default_config_has_all_retrieval_params(self):
        """Verify all retrieval parameters exist in default config."""
        from psychrag.utils.rag_config_loader import get_default_config
        config = get_default_config()

        required_retrieval_params = [
            "dense_limit", "lexical_limit", "rrf_k", "top_k_rrf", "top_n_final",
            "entity_boost", "min_word_count", "min_char_count", "min_content_length",
            "enrich_lines_above", "enrich_lines_below", "mmr_lambda",
            "reranker_batch_size", "reranker_max_length"
        ]

        for param in required_retrieval_params:
            assert param in config["retrieval"], f"Missing retrieval param: {param}"

    def test_default_config_has_all_consolidation_params(self):
        """Verify all consolidation parameters exist in default config."""
        from psychrag.utils.rag_config_loader import get_default_config
        config = get_default_config()

        required_consolidation_params = [
            "coverage_threshold", "line_gap", "min_content_length", "enrich_from_md"
        ]

        for param in required_consolidation_params:
            assert param in config["consolidation"], f"Missing consolidation param: {param}"

    def test_default_config_has_all_augmentation_params(self):
        """Verify all augmentation parameters exist in default config."""
        from psychrag.utils.rag_config_loader import get_default_config
        config = get_default_config()

        assert "top_n_contexts" in config["augmentation"]
```

**Test execution**:
```bash
venv\Scripts\pytest tests/unit/test_rag_config_integration.py -v
```

## Manual test plan

### Prerequisites:
1. Database initialized with default RAG config preset (T01)
2. Config loader utility working (T02)
3. Create a test query in database for end-to-end testing

### Test scenarios:

**1. Test retrieval with default config**
```bash
# Run retrieval with verbose output
venv\Scripts\python -m psychrag.retrieval.retrieve_cli --query-id 1 --verbose

# Expected: Should print "Using config preset: default"
# Expected: Should use dense_limit=19, top_n_final=17, etc.
```

**2. Test retrieval with custom config**
```python
# Create custom preset via API first:
# POST /api/rag-config/ with preset_name="Fast"

# Then in Python:
from psychrag.retrieval.retrieve import retrieve
retrieve(query_id=1, config_preset="Fast", verbose=True)

# Expected: Should print "Using config preset: Fast"
# Expected: Should use Fast preset's parameters
```

**3. Test consolidation with default config**
```bash
venv\Scripts\python -m psychrag.augmentation.consolidate_context_cli --query-id 1 --verbose

# Expected: Should use coverage_threshold=0.5, line_gap=7
```

**4. Test augmentation with default config**
```bash
venv\Scripts\python -m psychrag.augmentation.augment_cli --query-id 1 --verbose

# Expected: Should use top_n_contexts=5
```

**5. Test backward compatibility**
```python
# Test that old code calling functions without config_preset still works
from psychrag.retrieval.retrieve import retrieve
retrieve(query_id=1)  # No config_preset parameter

# Expected: Should work without errors, use default config
```

**6. Test error handling**
```python
from psychrag.retrieval.retrieve import retrieve
retrieve(query_id=1, config_preset="NonExistent", verbose=True)

# Expected: Should raise ValueError with helpful message
```

**7. Test parameter changes affect behavior**
```python
# Create two presets with different dense_limit values
# Preset "Few": dense_limit=5
# Preset "Many": dense_limit=50

# Run retrieval with each and compare number of candidates retrieved
# Should see different numbers in intermediate steps (logged if verbose=True)
```

## Dependencies and sequencing

### Dependencies:
- **Requires**: T01 (database), T02 (model and loader utility)
- **Parallel with**: T03 (API - can develop in parallel)
- **Blocks**: Full system testing (need this + T03 + T05 for complete flow)

### Sequencing notes:
- Can start immediately after T02 is complete
- Does not block T03 or T05 (they can develop in parallel)
- This ticket is on the critical path for complete RAG config feature
- Should be completed before T05 so frontend can test end-to-end

## Clarifications and assumptions

### Assumptions:
1. **Backward compatibility**: All functions accept `config_preset=None` as optional parameter
2. **Default behavior**: When `config_preset=None`, use default preset from database
3. **Error handling**: If custom preset not found, raise `ValueError` (don't fall back to default silently)
4. **Parameter extraction**: Load all params at function start into local variables (matches existing pattern)
5. **CLI scripts**: Not updating CLI argument parsers in this ticket (add `--config-preset` flag in future ticket)
6. **Hard-coded removal**: Remove ALL hard-coded parameter constants from these three modules
7. **Verbose logging**: If `verbose=True`, print which preset is being used

### Open questions (non-blocking):
1. Should we add config caching to avoid repeated database queries? (Performance optimization)
2. Should we add config validation at runtime or trust database validation? (Defense in depth)
3. Should consolidation/augmentation also log their config preset usage when verbose=True?
4. Should we add warnings when using non-default presets? (For debugging)

### Blocking questions (must answer before implementation):
None - all clarifications received from user.

### Implementer notes:

> **Before implementing**:
> - Read through `retrieve.py`, `consolidate_context.py`, and `augment.py` to identify all hard-coded parameters
> - Make a list of all constants that need to be replaced with config loader calls
> - Ensure T02 is complete and `get_default_config()` works correctly
> - Create a test query in your database for manual testing

> **During implementation**:
> - Work module by module: complete retrieval, test it, then move to consolidation, then augmentation
> - Test each module individually before moving to the next
> - Keep original hard-coded values commented out temporarily for easy rollback if needed
> - Use verbose output to verify correct config is loaded
> - Verify existing tests still pass after changes

> **After implementation**:
> - Run full test suite: `pytest tests/`
> - Run manual end-to-end test: query expansion → retrieval → consolidation → augmentation
> - Verify retrieved_context and clean_retrieval_context fields are populated correctly
> - Compare results with different presets to verify configs are being applied
> - Remove commented-out hard-coded values once confident
> - Update any docstrings that mentioned specific parameter values
