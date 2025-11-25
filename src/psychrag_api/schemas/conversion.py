"""
Pydantic schemas for Conversion router.
"""

from typing import Any

from pydantic import BaseModel, Field


class SupportedFormatsResponse(BaseModel):
    """Response listing supported conversion formats."""

    input_formats: list[str] = Field(
        ...,
        description="Supported input formats",
        example=["epub", "pdf"],
    )
    output_formats: list[str] = Field(
        ...,
        description="Supported output formats",
        example=["markdown"],
    )
    converters: dict[str, Any] = Field(
        default_factory=dict,
        description="Details about each converter",
        example={
            "epub": {
                "description": "EPUB e-book format",
                "extensions": [".epub"],
            }
        },
    )


class ConversionJobResponse(BaseModel):
    """Response for a conversion job submission."""

    job_id: str = Field(
        ...,
        description="Unique identifier for the conversion job",
        example="conv_epub_12345",
    )
    status: str = Field(
        ...,
        description="Current job status",
        example="queued",
    )
    message: str = Field(
        ...,
        description="Status message",
        example="Conversion job queued successfully",
    )
    input_filename: str = Field(
        ...,
        description="Original input filename",
        example="cognitive_psychology.epub",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "conv_epub_12345",
                "status": "queued",
                "message": "Conversion job queued successfully",
                "input_filename": "cognitive_psychology.epub",
            }
        }


class ConversionStatusResponse(BaseModel):
    """Response for conversion job status query."""

    job_id: str = Field(
        ...,
        description="Job identifier",
        example="conv_epub_12345",
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
    output_path: str | None = Field(
        default=None,
        description="Path to output file (if completed)",
        example="/output/cognitive_psychology.md",
    )
    error: str | None = Field(
        default=None,
        description="Error message (if failed)",
    )
    message: str | None = Field(
        default=None,
        description="Status message",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "conv_epub_12345",
                "status": "completed",
                "progress": 100,
                "output_path": "/output/cognitive_psychology.md",
                "message": "Conversion completed successfully",
            }
        }


