"""
Integration tests for RAG config loader in pipeline modules.

Tests that retrieval, consolidation, and augmentation modules
properly load and use configuration from database.
"""

import pytest
from unittest.mock import Mock, patch

from psychrag.utils.rag_config_loader import get_default_config, get_config_by_name
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

    def test_default_config_loads_successfully(self):
        """Test that default config can be loaded."""
        config = get_default_config()

        assert config is not None
        assert "retrieval" in config
        assert config["retrieval"]["dense_limit"] == 19  # Default value
        assert config["retrieval"]["top_n_final"] == 17

    def test_custom_preset_loads_successfully(self, test_config_preset):
        """Test that custom preset can be loaded."""
        config = get_config_by_name(test_config_preset)

        assert config is not None
        assert config["retrieval"]["dense_limit"] == 5  # Custom value
        assert config["retrieval"]["top_n_final"] == 5

    def test_invalid_preset_raises_error(self):
        """Test that invalid preset name raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            get_config_by_name("NonExistentPreset")


class TestConsolidationConfigIntegration:
    """Test config loading in consolidation module."""

    def test_consolidation_default_config(self):
        """Test that consolidation can load default config."""
        config = get_default_config()

        assert config["consolidation"]["coverage_threshold"] == 0.5
        assert config["consolidation"]["line_gap"] == 7
        assert config["consolidation"]["enrich_from_md"] is True

    def test_consolidation_custom_preset(self, test_config_preset):
        """Test that consolidation can load custom preset."""
        config = get_config_by_name(test_config_preset)

        assert config["consolidation"]["coverage_threshold"] == 0.6
        assert config["consolidation"]["line_gap"] == 3
        assert config["consolidation"]["enrich_from_md"] is False


class TestAugmentationConfigIntegration:
    """Test config loading in augmentation module."""

    def test_augment_default_config(self):
        """Test that augment functions can load default config."""
        config = get_default_config()

        assert config["augmentation"]["top_n_contexts"] == 5

    def test_augment_custom_preset(self, test_config_preset):
        """Test that augment functions can load custom preset."""
        config = get_config_by_name(test_config_preset)

        assert config["augmentation"]["top_n_contexts"] == 3


class TestBackwardCompatibility:
    """Test that existing code continues to work."""

    def test_config_loader_backward_compatible(self):
        """Test calling config loader without preset parameter."""
        # Should not raise error - uses default config
        try:
            config = get_default_config()
            assert config is not None
        except Exception as e:
            pytest.fail(f"Backward compatibility broken: {e}")


class TestConfigParameterValidation:
    """Test that loaded configs have expected structure."""

    def test_default_config_has_all_retrieval_params(self):
        """Verify all retrieval parameters exist in default config."""
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
        config = get_default_config()

        required_consolidation_params = [
            "coverage_threshold", "line_gap", "min_content_length", "enrich_from_md"
        ]

        for param in required_consolidation_params:
            assert param in config["consolidation"], f"Missing consolidation param: {param}"

    def test_default_config_has_all_augmentation_params(self):
        """Verify all augmentation parameters exist in default config."""
        config = get_default_config()

        assert "top_n_contexts" in config["augmentation"]

    def test_config_values_within_expected_ranges(self):
        """Test that config values are within reasonable ranges."""
        config = get_default_config()

        # Retrieval params should be positive
        assert config["retrieval"]["dense_limit"] > 0
        assert config["retrieval"]["top_n_final"] > 0
        assert 0.0 <= config["retrieval"]["mmr_lambda"] <= 1.0

        # Consolidation params
        assert 0.0 <= config["consolidation"]["coverage_threshold"] <= 1.0
        assert config["consolidation"]["line_gap"] >= 0

        # Augmentation params
        assert config["augmentation"]["top_n_contexts"] > 0


class TestModuleFunctionSignatures:
    """Test that module functions accept config_preset parameter."""

    def test_retrieve_accepts_config_preset(self):
        """Test that retrieve function signature includes config_preset."""
        from psychrag.retrieval.retrieve import retrieve
        import inspect

        sig = inspect.signature(retrieve)
        assert "config_preset" in sig.parameters

    def test_consolidate_accepts_config_preset(self):
        """Test that consolidate_context function signature includes config_preset."""
        from psychrag.augmentation.consolidate_context import consolidate_context
        import inspect

        sig = inspect.signature(consolidate_context)
        assert "config_preset" in sig.parameters

    def test_augment_accepts_config_preset(self):
        """Test that get_query_with_context function signature includes config_preset."""
        from psychrag.augmentation.augment import get_query_with_context
        import inspect

        sig = inspect.signature(get_query_with_context)
        assert "config_preset" in sig.parameters
