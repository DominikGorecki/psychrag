"""
Common/shared Pydantic schemas used across multiple routers.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response with common fields."""

    message: str | None = Field(
        default=None,
        description="Optional message providing additional context",
        example="Operation completed successfully",
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str = Field(
        ...,
        description="Error type/code",
        example="ValidationError",
    )
    detail: str = Field(
        ...,
        description="Human-readable error description",
        example="Invalid input: file must be a PDF",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the error occurred",
    )
    path: str | None = Field(
        default=None,
        description="API path where error occurred",
        example="/conv/pdf",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "detail": "Invalid file format. Expected PDF.",
                "timestamp": "2024-01-15T10:30:00Z",
                "path": "/conv/pdf",
            }
        }


class JobStatusResponse(BaseModel):
    """Response for async job status queries."""

    job_id: str = Field(
        ...,
        description="Unique job identifier",
        example="job_abc123",
    )
    status: str = Field(
        ...,
        description="Current job status",
        example="processing",
    )
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Progress percentage (0-100)",
        example=45,
    )
    created_at: datetime | None = Field(
        default=None,
        description="When the job was created",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="When the job was last updated",
    )
    message: str | None = Field(
        default=None,
        description="Status message",
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T] = Field(
        ...,
        description="List of items in current page",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of items",
        example=100,
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number",
        example=1,
    )
    page_size: int = Field(
        ...,
        ge=1,
        description="Items per page",
        example=20,
    )
    total_pages: int = Field(
        ...,
        ge=0,
        description="Total number of pages",
        example=5,
    )


class FilePathRequest(BaseModel):
    """Request containing a file path."""

    file_path: str = Field(
        ...,
        description="Path to the file",
        example="/output/document.md",
    )


class WorkIdentifier(BaseModel):
    """Identifier for a work/document."""

    work_id: str | None = Field(
        default=None,
        description="Work ID in the database",
        example="work_123",
    )
    file_path: str | None = Field(
        default=None,
        description="Path to the work file",
        example="/output/cognitive_psych.md",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "work_id": "work_123",
                "file_path": "/output/cognitive_psych.md",
            }
        }


