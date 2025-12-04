"""
Unit tests for PsychRAG API endpoints.

Tests all router endpoints with stub responses.

Usage:
    venv\\Scripts\\pytest tests/unit/test_api_endpoints.py -v
"""

import pytest
from fastapi.testclient import TestClient

from psychrag_api.main import app

client = TestClient(app)


class TestRootEndpoints:
    """Test root-level endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "redoc" in data

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestInitRouter:
    """Test /init endpoints."""

    def test_get_init_status(self):
        """Test initialization status endpoint."""
        response = client.get("/init/status")
        assert response.status_code == 200
        data = response.json()
        assert "database_initialized" in data
        assert "embeddings_ready" in data
        assert "models_loaded" in data

    def test_init_database(self):
        """Test database initialization endpoint."""
        response = client.post(
            "/init/database",
            json={"reset": False, "create_indexes": True}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "tables_created" in data

    def test_detailed_health_check(self):
        """Test detailed health check endpoint."""
        response = client.get("/init/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data


class TestSettingsRouter:
    """Test /settings endpoints."""

    def test_get_all_settings(self):
        """Test get all settings endpoint."""
        response = client.get("/settings/")
        assert response.status_code == 200
        data = response.json()
        # Verify top-level structure matches AppConfigSchema
        assert "database" in data
        assert "llm" in data
        assert "paths" in data
        assert isinstance(data["database"], dict)
        assert isinstance(data["llm"], dict)
        assert isinstance(data["paths"], dict)
        # Verify database structure
        assert "admin_user" in data["database"]
        assert "host" in data["database"]
        assert "port" in data["database"]
        assert "db_name" in data["database"]
        assert "app_user" in data["database"]
        # Verify llm structure
        assert "provider" in data["llm"]
        assert "models" in data["llm"]
        # Verify paths structure
        assert "input_dir" in data["paths"]
        assert "output_dir" in data["paths"]

    def test_get_nonexistent_setting(self):
        """Test get nonexistent setting returns 404."""
        response = client.get("/settings/nonexistent_key")
        assert response.status_code == 404


class TestConversionRouter:
    """Test /conv endpoints."""

    pass





class TestChunkingRouter:
    """Test /chunk endpoints."""
    
    # Note: Legacy file-path-based endpoint tests have been removed as they don't exist in the API.
    # The current API uses work-based endpoints (e.g., /chunking/work/{work_id}/apply-heading-chunks).
    # Tests for work-based endpoints can be added in a follow-up ticket if needed.


class TestVectorizationRouter:
    """Test /vec endpoints."""

    def test_list_embedding_models(self):
        """Test list embedding models endpoint."""
        response = client.get("/vec/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "default_model" in data
        assert len(data["models"]) > 0

    def test_vectorize_chunks(self):
        """Test chunk vectorization endpoint."""
        response = client.post(
            "/vec/chunks",
            json={"chunk_ids": ["chunk_001", "chunk_002"]}
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["chunks_queued"] == 2

    def test_vectorize_query(self):
        """Test query vectorization endpoint."""
        response = client.post(
            "/vec/query",
            json={"query": "What is cognitive load?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "What is cognitive load?"
        assert "embedding" in data
        assert "dimensions" in data

    def test_get_vectorization_status(self):
        """Test vectorization status endpoint."""
        response = client.get("/vec/status/vec_12345")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "vec_12345"
        assert "status" in data


class TestRAGRouter:
    """Test /rag endpoints."""
    
    # Note: Legacy action-based endpoint tests have been removed as they don't exist in the API.
    # The current API uses query-based endpoints (e.g., /rag/queries, /rag/queries/{id}/retrieve).
    # Tests for query-based endpoints can be added in a follow-up ticket if needed.


class TestOpenAPIDocumentation:
    """Test OpenAPI documentation endpoints."""

    def test_openapi_json_available(self):
        """Test OpenAPI JSON is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "info" in data

    def test_swagger_ui_available(self):
        """Test Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_available(self):
        """Test ReDoc is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_has_all_tags(self):
        """Test OpenAPI has all expected tags."""
        response = client.get("/openapi.json")
        data = response.json()
        tag_names = [tag["name"] for tag in data.get("tags", [])]
        expected_tags = [
            "Init", "Settings", "Conversion", "Sanitization",
            "Chunking", "Vectorization", "RAG"
        ]
        for tag in expected_tags:
            assert tag in tag_names, f"Missing tag: {tag}"


