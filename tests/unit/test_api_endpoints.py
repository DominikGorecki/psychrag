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
        assert "settings" in data
        assert isinstance(data["settings"], dict)

    def test_get_specific_setting(self):
        """Test get specific setting endpoint."""
        response = client.get("/settings/embedding_model")
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "embedding_model"
        assert "value" in data

    def test_get_nonexistent_setting(self):
        """Test get nonexistent setting returns 404."""
        response = client.get("/settings/nonexistent_key")
        assert response.status_code == 404

    def test_update_setting(self):
        """Test update setting endpoint."""
        response = client.put(
            "/settings/chunk_size",
            json={"value": 1024}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "chunk_size"
        assert data["value"] == 1024


class TestConversionRouter:
    """Test /conv endpoints."""

    pass





class TestChunkingRouter:
    """Test /chunk endpoints."""

    def test_chunk_by_headings(self):
        """Test heading-based chunking endpoint."""
        response = client.post(
            "/chunk/headings",
            json={"file_path": "/output/test.md", "min_level": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert "chunks" in data
        assert "total_chunks" in data

    def test_chunk_by_content(self):
        """Test content-based chunking endpoint."""
        response = client.post(
            "/chunk/content",
            json={"file_path": "/output/test.md", "chunk_size": 512}
        )
        assert response.status_code == 200
        data = response.json()
        assert "chunks" in data
        assert "total_tokens" in data

    def test_suggest_chunks(self):
        """Test chunk suggestion endpoint."""
        response = client.post(
            "/chunk/suggest",
            json={"file_path": "/output/test.md"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

    def test_extract_bibliography(self):
        """Test bibliography extraction endpoint."""
        response = client.post(
            "/chunk/extract-bib",
            json={"file_path": "/output/test.md"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total_entries" in data

    def test_process_llm(self):
        """Test LLM processing endpoint."""
        response = client.post(
            "/chunk/process-llm",
            json={"chunk_ids": ["chunk_001"], "operation": "summarize"}
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["operation"] == "summarize"


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

    def test_rag_query(self):
        """Test full RAG query endpoint."""
        response = client.post(
            "/rag/query",
            json={"query": "What is cognitive load theory?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "What is cognitive load theory?"
        assert "answer" in data
        assert "sources" in data

    def test_retrieve_chunks(self):
        """Test chunk retrieval endpoint."""
        response = client.post(
            "/rag/retrieve",
            json={"query": "working memory", "top_k": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert "chunks" in data
        assert "total_retrieved" in data

    def test_expand_query(self):
        """Test query expansion endpoint."""
        response = client.post(
            "/rag/expand-query",
            json={"query": "cognitive load"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["original_query"] == "cognitive load"
        assert "expanded_queries" in data
        assert len(data["expanded_queries"]) > 0

    def test_augment_content(self):
        """Test content augmentation endpoint."""
        response = client.post(
            "/rag/augment",
            json={"content": "Cognitive load refers to..."}
        )
        assert response.status_code == 200
        data = response.json()
        assert "augmented_content" in data
        assert "context_added" in data

    def test_generate_response(self):
        """Test response generation endpoint."""
        response = client.post(
            "/rag/generate",
            json={
                "query": "Summarize memory",
                "context_chunks": ["chunk_001", "chunk_002"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["context_chunks_used"] == 2


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


