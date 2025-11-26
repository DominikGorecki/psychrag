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


class IOFolderDataResponse(BaseModel):
    """Response containing input and processed file data."""

    input_files: list[str] = Field(
        default_factory=list,
        description="List of unprocessed input files",
        example=["cognitive_psychology.pdf", "memory_handbook.pdf"],
    )
    processed_files: list[str] = Field(
        default_factory=list,
        description="List of processed files in pipe-separated format: basename|id|variant1|variant2|...",
        example=["test|42|.pdf|.style.md|.hier.md|.toc_titles.md"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "input_files": ["cognitive_psychology.pdf", "memory_handbook.pdf"],
                "processed_files": [
                    "learning_theory|42|.pdf|.style.md|.hier.md|.toc_titles.md",
                    "perception_basics|43|.pdf|.style.md|.toc_titles.md"
                ],
            }
        }


class ConvertFileRequest(BaseModel):
    """Request to convert a file."""

    filename: str = Field(
        ...,
        description="Name of the file to convert (must exist in input directory)",
        example="cognitive_psychology.pdf",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "cognitive_psychology.pdf",
            }
        }


class ConvertFileResponse(BaseModel):
    """Response after file conversion."""

    success: bool = Field(
        ...,
        description="Whether the conversion was successful",
        example=True,
    )
    message: str = Field(
        ...,
        description="Status message",
        example="Conversion completed successfully",
    )
    input_file: str = Field(
        ...,
        description="Input filename that was converted",
        example="cognitive_psychology.pdf",
    )
    output_files: list[str] = Field(
        default_factory=list,
        description="List of output files created",
        example=["cognitive_psychology.pdf", "cognitive_psychology.style.md", "cognitive_psychology.hier.md"],
    )
    error: str | None = Field(
        default=None,
        description="Error message if conversion failed",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Conversion completed successfully",
                "input_file": "cognitive_psychology.pdf",
                "output_files": [
                    "cognitive_psychology.pdf",
                    "cognitive_psychology.style.md",
                    "cognitive_psychology.hier.md",
                    "cognitive_psychology.toc_titles.md"
                ],
            }
        }


class InspectionItemSchema(BaseModel):
    """Schema for a single inspection item."""

    name: str = Field(
        ...,
        description="Machine-readable inspection name",
        example="inspect_style_hier",
    )
    available: bool = Field(
        ...,
        description="Whether the required files exist for this inspection",
        example=True,
    )
    files_checked: list[str] = Field(
        default_factory=list,
        description="List of filenames that were checked for this inspection",
        example=["test.style.md", "test.hier.md"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "inspect_style_hier",
                "available": True,
                "files_checked": ["test.style.md", "test.hier.md"],
            }
        }


class ConversionInspectionResponse(BaseModel):
    """Response containing inspection options for a converted file."""

    items: list[InspectionItemSchema] = Field(
        default_factory=list,
        description="List of inspection items in priority order",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "name": "inspect_style_hier",
                        "available": True,
                        "files_checked": ["test.style.md", "test.hier.md"],
                    },
                    {
                        "name": "inspect_toc_titles",
                        "available": True,
                        "files_checked": ["test.toc_titles.md"],
                    },
                    {
                        "name": "inspect_titles",
                        "available": False,
                        "files_checked": ["test.titles.md"],
                    },
                    {
                        "name": "inspect_title_changes",
                        "available": False,
                        "files_checked": ["test.title_changes.md"],
                    },
                    {
                        "name": "inspect_original_md",
                        "available": True,
                        "files_checked": ["test.md"],
                    },
                ]
            }
        }


class FileContentResponse(BaseModel):
    """Response containing markdown file content."""

    content: str = Field(
        ...,
        description="Markdown file content",
        example="# Heading\n\nContent here...",
    )
    filename: str = Field(
        ...,
        description="Filename of the content",
        example="test.style.md",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "# Chapter 1\n\n## Introduction\n\nThis is the content...",
                "filename": "test.style.md",
            }
        }


class FileContentUpdateRequest(BaseModel):
    """Request to update markdown file content."""

    content: str = Field(
        ...,
        description="New markdown content to save",
        example="# Updated Heading\n\nNew content...",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "# Updated Chapter 1\n\n## Introduction\n\nThis is the updated content...",
            }
        }


class FileMetricsSchema(BaseModel):
    """Structural metrics for a markdown file."""

    total_headings: int = Field(..., description="Total number of headings")
    h1_h2_count: int = Field(..., description="Number of H1 and H2 headings")
    max_depth: int = Field(..., description="Maximum heading depth")
    avg_depth: float = Field(..., description="Average heading depth")
    coverage_score: float = Field(..., description="Coverage score (0-1)")
    hierarchy_score: float = Field(..., description="Hierarchy score (0-1)")
    chunkability_score: float = Field(..., description="Chunkability score (0-1)")
    target_size_sections: int = Field(..., description="Number of target-sized sections")
    small_sections: int = Field(..., description="Number of small sections")
    large_sections: int = Field(..., description="Number of large sections")
    level_jump_count: int = Field(..., description="Number of level jumps")
    penalty_total: float = Field(..., description="Total penalties applied")
    final_score: float = Field(..., description="Final weighted score")


class FileSuggestionResponse(BaseModel):
    """Response containing comparison metrics and suggestion."""

    style_metrics: FileMetricsSchema = Field(
        ...,
        description="Metrics for style.md file",
    )
    hier_metrics: FileMetricsSchema = Field(
        ...,
        description="Metrics for hier.md file",
    )
    winner: str = Field(
        ...,
        description="Suggested winner: 'style' or 'hier'",
        example="hier",
    )
    score_difference: float = Field(
        ...,
        description="Absolute difference between scores",
        example=0.15,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "style_metrics": {
                    "total_headings": 45,
                    "h1_h2_count": 8,
                    "max_depth": 4,
                    "avg_depth": 2.5,
                    "coverage_score": 0.75,
                    "hierarchy_score": 0.82,
                    "chunkability_score": 0.65,
                    "target_size_sections": 20,
                    "small_sections": 10,
                    "large_sections": 5,
                    "level_jump_count": 3,
                    "penalty_total": 5.0,
                    "final_score": 0.72,
                },
                "hier_metrics": {
                    "total_headings": 52,
                    "h1_h2_count": 10,
                    "max_depth": 4,
                    "avg_depth": 2.8,
                    "coverage_score": 0.85,
                    "hierarchy_score": 0.88,
                    "chunkability_score": 0.78,
                    "target_size_sections": 28,
                    "small_sections": 8,
                    "large_sections": 3,
                    "level_jump_count": 2,
                    "penalty_total": 0.0,
                    "final_score": 0.84,
                },
                "winner": "hier",
                "score_difference": 0.12,
            }
        }


class FileSelectionRequest(BaseModel):
    """Request to select a file as the main version."""

    file_type: str = Field(
        ...,
        description="Type of file to select: 'style' or 'hier'",
        example="hier",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_type": "hier",
            }
        }


class FileSelectionResponse(BaseModel):
    """Response after selecting a file."""

    success: bool = Field(
        ...,
        description="Whether the selection was successful",
        example=True,
    )
    message: str = Field(
        ...,
        description="Status message",
        example="Successfully copied hier.md to test.md",
    )
    output_file: str = Field(
        ...,
        description="Path to the output file created",
        example="test.md",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully copied hier.md to test.md",
                "output_file": "test.md",
            }
        }


