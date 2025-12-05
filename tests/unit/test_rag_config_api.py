"""
Unit tests for RAG Config API endpoints.

Tests all CRUD operations and validation.
"""

import pytest
from fastapi.testclient import TestClient

from psychrag_api.main import app
from psychrag.data.database import get_session
from psychrag.data.models.rag_config import RagConfig

client = TestClient(app)


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


class TestListPresets:
    """Test GET /api/rag-config/ endpoint."""

    def test_list_presets_success(self):
        """Test successful listing of all presets."""
        response = client.get("/api/rag-config/")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("preset_name" in item for item in data)

    def test_list_presets_default_first(self):
        """Test that default preset appears first in list."""
        response = client.get("/api/rag-config/")
        data = response.json()

        # First item should be default
        assert data[0]["is_default"] is True


class TestGetDefaultPreset:
    """Test GET /api/rag-config/default endpoint."""

    def test_get_default_success(self):
        """Test successful retrieval of default preset."""
        response = client.get("/api/rag-config/default")
        assert response.status_code == 200

        data = response.json()
        assert data["is_default"] is True
        assert "config" in data
        assert "retrieval" in data["config"]


class TestGetPresetByName:
    """Test GET /api/rag-config/{preset_name} endpoint."""

    def test_get_preset_by_name_success(self):
        """Test successful retrieval by name."""
        response = client.get("/api/rag-config/Default")
        assert response.status_code == 200

        data = response.json()
        assert data["preset_name"] == "Default"

    def test_get_preset_by_name_not_found(self):
        """Test 404 for non-existent preset."""
        response = client.get("/api/rag-config/NonExistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreatePreset:
    """Test POST /api/rag-config/ endpoint."""

    def test_create_preset_success(self):
        """Test successful preset creation."""
        payload = {
            "preset_name": "TestCreate",
            "description": "Test preset",
            "is_default": False,
            "config": {
                "retrieval": {
                    "dense_limit": 10,
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
        }

        response = client.post("/api/rag-config/", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["preset_name"] == "TestCreate"
        assert data["config"]["retrieval"]["dense_limit"] == 10

        # Cleanup
        client.delete("/api/rag-config/TestCreate")

    def test_create_preset_duplicate_name(self):
        """Test 409 conflict for duplicate name."""
        payload = {
            "preset_name": "Default",  # Existing preset
            "is_default": False,
            "config": {
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
        }

        response = client.post("/api/rag-config/", json=payload)
        assert response.status_code == 409

    def test_create_preset_validation_error(self):
        """Test validation errors for invalid parameters."""
        payload = {
            "preset_name": "InvalidParams",
            "is_default": False,
            "config": {
                "retrieval": {
                    "dense_limit": 999,  # Exceeds max of 100
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
        }

        response = client.post("/api/rag-config/", json=payload)
        assert response.status_code == 422  # Validation error


class TestUpdatePreset:
    """Test PUT /api/rag-config/{preset_name} endpoint."""

    @pytest.fixture(autouse=True)
    def setup_test_preset(self):
        """Create test preset for update tests."""
        payload = {
            "preset_name": "TestUpdate",
            "is_default": False,
            "config": {
                "retrieval": {
                    "dense_limit": 15,
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
                    "line_gap": 5,
                    "min_content_length": 350,
                    "enrich_from_md": True
                },
                "augmentation": {
                    "top_n_contexts": 3
                }
            }
        }
        client.post("/api/rag-config/", json=payload)
        yield
        client.delete("/api/rag-config/TestUpdate")

    def test_update_preset_description(self):
        """Test updating preset description."""
        update_payload = {
            "description": "Updated description"
        }

        response = client.put("/api/rag-config/TestUpdate", json=update_payload)
        assert response.status_code == 200

        data = response.json()
        assert data["description"] == "Updated description"

    def test_update_preset_config(self):
        """Test updating preset config."""
        update_payload = {
            "config": {
                "retrieval": {
                    "dense_limit": 25,
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
                    "line_gap": 10,
                    "min_content_length": 350,
                    "enrich_from_md": True
                },
                "augmentation": {
                    "top_n_contexts": 7
                }
            }
        }

        response = client.put("/api/rag-config/TestUpdate", json=update_payload)
        assert response.status_code == 200

        data = response.json()
        assert data["config"]["retrieval"]["dense_limit"] == 25


class TestSetDefaultPreset:
    """Test PUT /api/rag-config/{preset_name}/set-default endpoint."""

    @pytest.fixture(autouse=True)
    def setup_test_preset(self):
        """Create test preset."""
        payload = {
            "preset_name": "TestDefault",
            "is_default": False,
            "config": {
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
        }
        client.post("/api/rag-config/", json=payload)
        yield
        # Reset default back
        client.put("/api/rag-config/Default/set-default")
        client.delete("/api/rag-config/TestDefault")

    def test_set_default_success(self):
        """Test setting preset as default."""
        response = client.put("/api/rag-config/TestDefault/set-default")
        assert response.status_code == 200

        data = response.json()
        assert data["is_default"] is True

        # Verify old default is now false
        default_response = client.get("/api/rag-config/default")
        assert default_response.json()["preset_name"] == "TestDefault"


class TestDeletePreset:
    """Test DELETE /api/rag-config/{preset_name} endpoint."""

    def test_delete_preset_success(self):
        """Test successful preset deletion."""
        # Create preset to delete
        payload = {
            "preset_name": "TestDelete",
            "is_default": False,
            "config": {
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
        }
        client.post("/api/rag-config/", json=payload)

        # Delete it
        response = client.delete("/api/rag-config/TestDelete")
        assert response.status_code == 204

        # Verify deleted
        get_response = client.get("/api/rag-config/TestDelete")
        assert get_response.status_code == 404

    def test_delete_default_preset_fails(self):
        """Test that deleting default preset is prevented."""
        response = client.delete("/api/rag-config/Default")
        assert response.status_code == 400
        assert "Cannot delete default" in response.json()["detail"]

    def test_delete_nonexistent_preset(self):
        """Test 404 for deleting non-existent preset."""
        response = client.delete("/api/rag-config/NonExistent")
        assert response.status_code == 404
