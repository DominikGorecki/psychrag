"""
Pydantic schemas for Init router.
"""

from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Database Health Check Schemas
# ============================================================================

class DbHealthCheckResult(BaseModel):
    """Result of a single health check."""

    name: str = Field(
        ...,
        description="Name of the health check",
        example="Connection",
    )
    passed: bool = Field(
        ...,
        description="Whether the check passed",
        example=True,
    )
    message: str = Field(
        ...,
        description="Status message",
        example="App user can connect to database",
    )
    details: str | None = Field(
        default=None,
        description="Additional details (usually for failures)",
        example=None,
    )


class DbHealthCheckResponse(BaseModel):
    """Response containing all database health check results."""

    results: list[DbHealthCheckResult] = Field(
        ...,
        description="List of all health check results",
    )
    all_passed: bool = Field(
        ...,
        description="Whether all checks passed",
        example=True,
    )
    connection_ok: bool = Field(
        ...,
        description="Whether the connection check passed (first check)",
        example=True,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {"name": "Connection", "passed": True, "message": "App user can connect to database", "details": None},
                    {"name": "Extension: vector", "passed": True, "message": "Extension 'vector' is installed", "details": None},
                ],
                "all_passed": True,
                "connection_ok": True,
            }
        }


# ============================================================================
# Init Status Schemas
# ============================================================================

class InitStatusResponse(BaseModel):
    """Response for system initialization status."""

    database_initialized: bool = Field(
        ...,
        description="Whether the database is initialized",
        example=True,
    )
    embeddings_ready: bool = Field(
        ...,
        description="Whether embedding models are loaded",
        example=True,
    )
    models_loaded: bool = Field(
        ...,
        description="Whether LLM models are configured",
        example=False,
    )
    message: str | None = Field(
        default=None,
        description="Additional status information",
        example="System partially initialized",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "database_initialized": True,
                "embeddings_ready": True,
                "models_loaded": False,
                "message": "System partially initialized - LLM not configured",
            }
        }


class DatabaseInitRequest(BaseModel):
    """Request to initialize the database."""

    reset: bool = Field(
        default=False,
        description="If True, drop and recreate all tables (WARNING: deletes data!)",
        example=False,
    )
    create_indexes: bool = Field(
        default=True,
        description="Whether to create database indexes",
        example=True,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reset": False,
                "create_indexes": True,
            }
        }


class DatabaseInitResponse(BaseModel):
    """Response for database initialization."""

    success: bool = Field(
        ...,
        description="Whether initialization was successful",
        example=True,
    )
    message: str = Field(
        ...,
        description="Status message",
        example="Database initialized successfully",
    )
    tables_created: list[str] = Field(
        default_factory=list,
        description="List of tables that were created/verified",
        example=["works", "chunks", "embeddings"],
    )


class ComponentHealth(BaseModel):
    """Health status of a single component."""

    status: str = Field(
        ...,
        description="Component status: healthy, degraded, unhealthy, unknown",
        example="healthy",
    )
    latency_ms: float | None = Field(
        default=None,
        description="Response latency in milliseconds",
        example=12.5,
    )
    error: str | None = Field(
        default=None,
        description="Error message if unhealthy",
    )


class HealthCheckResponse(BaseModel):
    """Detailed health check response."""

    status: str = Field(
        ...,
        description="Overall system status",
        example="healthy",
    )
    components: dict[str, Any] = Field(
        default_factory=dict,
        description="Health status of individual components",
        example={
            "database": {"status": "healthy", "latency_ms": 5.2},
            "embedding_model": {"status": "healthy", "latency_ms": 120.0},
            "llm": {"status": "degraded", "latency_ms": 2500.0},
        },
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "components": {
                    "database": {"status": "healthy", "latency_ms": 5.2},
                    "embedding_model": {"status": "healthy", "latency_ms": 120.0},
                    "llm": {"status": "healthy", "latency_ms": 450.0},
                },
            }
        }


