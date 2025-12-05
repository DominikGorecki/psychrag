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


@pytest.fixture(autouse=True)
def ensure_default_preset():
    """Ensure default preset exists before each test."""
    with get_session() as session:
        # Check if default preset exists
        default = session.query(RagConfig).filter(RagConfig.preset_name == "Default").first()
        if not default:
            # Create default preset if it doesn't exist
            default_preset = RagConfig(
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
            session.add(default_preset)
            session.commit()
        else:
            # Ensure it's marked as default
            if not default.is_default:
                default.is_default = True
                session.commit()


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
