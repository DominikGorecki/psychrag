"""
Pydantic schemas for Vectorization router.
"""

from typing import Any

from pydantic import BaseModel, Field


class EmbeddingModelInfo(BaseModel):
    """Information about an embedding model."""

    id: str = Field(..., description="Model identifier")
    provider: str = Field(..., description="Provider (openai, google, etc.)")
    dimensions: int = Field(..., description="Embedding dimensions")
    max_tokens: int = Field(..., description="Maximum input tokens")
    description: str | None = Field(None, description="Model description")


class EmbeddingModelsResponse(BaseModel):
    """Response listing available embedding models."""

    models: list[dict[str, Any]] = Field(
        ...,
        description="List of available embedding models",
    )
    default_model: str = Field(
        ...,
        description="Default model ID",
        example="text-embedding-3-small",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "models": [
                    {
                        "id": "text-embedding-3-small",
                        "provider": "openai",
                        "dimensions": 1536,
                        "max_tokens": 8191,
                        "description": "OpenAI's small embedding model",
                    },
                    {
                        "id": "text-embedding-3-large",
                        "provider": "openai",
                        "dimensions": 3072,
                        "max_tokens": 8191,
                        "description": "OpenAI's large embedding model",
                    },
                ],
                "default_model": "text-embedding-3-small",
            }
        }


class VectorizeChunksRequest(BaseModel):
    """Request to vectorize chunks."""

    chunk_ids: list[str] = Field(
        ...,
        description="List of chunk IDs to vectorize",
        example=["chunk_001", "chunk_002", "chunk_003"],
    )
    model: str | None = Field(
        default=None,
        description="Embedding model to use (defaults to configured model)",
        example="text-embedding-3-small",
    )
    store: bool = Field(
        default=True,
        description="Whether to store embeddings in database",
        example=True,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_ids": ["chunk_001", "chunk_002", "chunk_003"],
                "model": "text-embedding-3-small",
                "store": True,
            }
        }


class VectorizeChunksResponse(BaseModel):
    """Response for chunk vectorization job."""

    job_id: str = Field(
        ...,
        description="Unique job identifier",
        example="vec_12345",
    )
    status: str = Field(
        ...,
        description="Job status",
        example="queued",
    )
    chunks_queued: int = Field(
        ...,
        description="Number of chunks queued",
        example=3,
    )
    model: str = Field(
        ...,
        description="Embedding model being used",
        example="text-embedding-3-small",
    )
    message: str | None = Field(default=None)


class VectorizeQueryRequest(BaseModel):
    """Request to vectorize a query string."""

    query: str = Field(
        ...,
        description="Query text to vectorize",
        example="What is cognitive load theory?",
    )
    model: str | None = Field(
        default=None,
        description="Embedding model to use",
        example="text-embedding-3-small",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is cognitive load theory?",
                "model": "text-embedding-3-small",
            }
        }


class VectorizeQueryResponse(BaseModel):
    """Response containing query embedding."""

    query: str = Field(
        ...,
        description="Original query text",
        example="What is cognitive load theory?",
    )
    model: str = Field(
        ...,
        description="Model used for embedding",
        example="text-embedding-3-small",
    )
    dimensions: int = Field(
        ...,
        description="Embedding dimensions",
        example=1536,
    )
    embedding: list[float] = Field(
        ...,
        description="Embedding vector (truncated in examples)",
    )
    message: str | None = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is cognitive load theory?",
                "model": "text-embedding-3-small",
                "dimensions": 1536,
                "embedding": [0.01, -0.02, 0.03],  # Truncated
                "message": "Note: embedding truncated in example",
            }
        }


class VectorizationStatusResponse(BaseModel):
    """Response for vectorization job status."""

    job_id: str = Field(
        ...,
        description="Job identifier",
        example="vec_12345",
    )
    status: str = Field(
        ...,
        description="Current status: queued, processing, completed, failed",
        example="completed",
    )
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Progress percentage",
        example=100,
    )
    chunks_processed: int = Field(
        default=0,
        description="Chunks processed so far",
        example=10,
    )
    chunks_total: int = Field(
        default=0,
        description="Total chunks to process",
        example=10,
    )
    message: str | None = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "vec_12345",
                "status": "completed",
                "progress": 100,
                "chunks_processed": 10,
                "chunks_total": 10,
                "message": "Vectorization complete",
            }
        }


