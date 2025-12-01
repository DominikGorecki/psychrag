"""
Unit tests for RAG config database schema and constraints.

Tests table structure, triggers, and data integrity.

Note: These tests will work once T02 (RagConfig model) is implemented.
Until then, some tests using the model will be skipped.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from psychrag.data.database import engine, get_session

# Try to import RagConfig model (will fail until T02 is complete)
try:
    from psychrag.data.models.rag_config import RagConfig
    HAS_MODEL = True
except ImportError:
    HAS_MODEL = False


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
        with engine.connect() as conn:
            # Create first preset using raw SQL
            conn.execute(text("""
                INSERT INTO rag_config (preset_name, is_default, config)
                VALUES ('TestUnique', FALSE, '{"retrieval":{}, "consolidation":{}, "augmentation":{}}')
            """))
            conn.commit()

            # Try to create duplicate - should fail
            with pytest.raises(IntegrityError):
                conn.execute(text("""
                    INSERT INTO rag_config (preset_name, is_default, config)
                    VALUES ('TestUnique', FALSE, '{"retrieval":{}, "consolidation":{}, "augmentation":{}}')
                """))
                conn.commit()

            # Cleanup
            conn.rollback()
            conn.execute(text("DELETE FROM rag_config WHERE preset_name = 'TestUnique'"))
            conn.commit()

    def test_single_default_trigger(self):
        """Test that only one preset can have is_default=True."""
        with engine.connect() as conn:
            # Create two presets, both marked as default
            conn.execute(text("""
                INSERT INTO rag_config (preset_name, is_default, config)
                VALUES ('TestDefault1', TRUE, '{"retrieval":{}, "consolidation":{}, "augmentation":{}}')
            """))
            conn.commit()

            conn.execute(text("""
                INSERT INTO rag_config (preset_name, is_default, config)
                VALUES ('TestDefault2', TRUE, '{"retrieval":{}, "consolidation":{}, "augmentation":{}}')
            """))
            conn.commit()

            # Query to verify only one is default
            result = conn.execute(text("SELECT COUNT(*) FROM rag_config WHERE is_default = TRUE"))
            default_count = result.scalar()
            assert default_count == 1

            # Verify the second one is the default (trigger should have unset the first)
            result = conn.execute(text(
                "SELECT preset_name FROM rag_config WHERE is_default = TRUE"
            ))
            default_name = result.scalar()
            assert default_name == 'TestDefault2'

            # Cleanup
            conn.execute(text("DELETE FROM rag_config WHERE preset_name IN ('TestDefault1', 'TestDefault2')"))
            conn.commit()

    def test_updated_at_trigger(self):
        """Test that updated_at is automatically set on UPDATE."""
        import time

        with engine.connect() as conn:
            # Create preset
            conn.execute(text("""
                INSERT INTO rag_config (preset_name, is_default, config)
                VALUES ('TestUpdate', FALSE, '{"retrieval":{}, "consolidation":{}, "augmentation":{}}')
            """))
            conn.commit()

            # Get original updated_at
            result = conn.execute(text(
                "SELECT updated_at FROM rag_config WHERE preset_name = 'TestUpdate'"
            ))
            original_updated_at = result.scalar()

            time.sleep(1)

            # Update preset
            conn.execute(text("""
                UPDATE rag_config SET description = 'Updated description'
                WHERE preset_name = 'TestUpdate'
            """))
            conn.commit()

            # Verify updated_at changed
            result = conn.execute(text(
                "SELECT updated_at FROM rag_config WHERE preset_name = 'TestUpdate'"
            ))
            new_updated_at = result.scalar()
            assert new_updated_at > original_updated_at

            # Cleanup
            conn.execute(text("DELETE FROM rag_config WHERE preset_name = 'TestUpdate'"))
            conn.commit()


class TestDefaultPresetSeed:
    """Test default preset seeding."""

    def test_default_preset_exists(self):
        """Verify default preset was created."""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT preset_name, is_default, description
                FROM rag_config
                WHERE preset_name = 'Default'
            """))
            row = result.fetchone()

            assert row is not None
            assert row[0] == 'Default'
            assert row[1] is True
            assert row[2] is not None

    def test_default_preset_has_all_params(self):
        """Verify default preset has all required parameters."""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT config
                FROM rag_config
                WHERE preset_name = 'Default'
            """))
            config = result.scalar()

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

    def test_default_preset_values(self):
        """Verify default preset has correct parameter values."""
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT config
                FROM rag_config
                WHERE preset_name = 'Default'
            """))
            config = result.scalar()

            # Check some key values
            assert config["retrieval"]["dense_limit"] == 19
            assert config["retrieval"]["lexical_limit"] == 5
            assert config["retrieval"]["top_n_final"] == 17
            assert config["consolidation"]["coverage_threshold"] == 0.5
            assert config["augmentation"]["top_n_contexts"] == 5


@pytest.mark.skipif(not HAS_MODEL, reason="RagConfig model not yet implemented (T02)")
class TestRagConfigWithModel:
    """Tests using the RagConfig SQLAlchemy model (requires T02)."""

    def test_preset_name_unique_constraint_with_model(self):
        """Test that duplicate preset names are rejected using model."""
        with get_session() as session:
            # Create first preset
            preset1 = RagConfig(
                preset_name="TestUniqueModel",
                is_default=False,
                config={"retrieval": {}, "consolidation": {}, "augmentation": {}}
            )
            session.add(preset1)
            session.commit()

            # Try to create duplicate
            with pytest.raises(IntegrityError):
                preset2 = RagConfig(
                    preset_name="TestUniqueModel",
                    is_default=False,
                    config={"retrieval": {}, "consolidation": {}, "augmentation": {}}
                )
                session.add(preset2)
                session.commit()

            # Cleanup
            session.rollback()
            session.query(RagConfig).filter(RagConfig.preset_name == "TestUniqueModel").delete()
            session.commit()

    def test_single_default_trigger_with_model(self):
        """Test that only one preset can have is_default=True using model."""
        with get_session() as session:
            # Create two presets, both marked as default
            preset1 = RagConfig(
                preset_name="TestDefaultModel1",
                is_default=True,
                config={"retrieval": {}, "consolidation": {}, "augmentation": {}}
            )
            preset2 = RagConfig(
                preset_name="TestDefaultModel2",
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
            assert defaults[0].preset_name == "TestDefaultModel2"

            # Cleanup
            session.query(RagConfig).filter(
                RagConfig.preset_name.in_(["TestDefaultModel1", "TestDefaultModel2"])
            ).delete()
            session.commit()

    def test_model_create_and_retrieve(self):
        """Test creating and retrieving a RagConfig instance."""
        with get_session() as session:
            config = RagConfig(
                preset_name="TestModelCreate",
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
            assert retrieved.preset_name == "TestModelCreate"
            assert retrieved.is_default is False
            assert retrieved.config["retrieval"]["dense_limit"] == 20

            # Cleanup
            session.delete(retrieved)
            session.commit()
