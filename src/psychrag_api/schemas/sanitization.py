"""
Pydantic schemas for Sanitization router.
"""

from typing import Any

from pydantic import BaseModel, Field


class ExtractTOCRequest(BaseModel):
    """Request to extract table of contents."""

    file_path: str = Field(
        ...,
        description="Path to the markdown file",
        example="/output/cognitive_psychology.md",
    )
    max_depth: int = Field(
        default=6,
        ge=1,
        le=6,
        description="Maximum heading depth to include",
        example=3,
    )


class TOCEntry(BaseModel):
    """A single TOC entry."""

    level: int = Field(..., description="Heading level (1-6)")
    title: str = Field(..., description="Heading text")
    line: int = Field(..., description="Line number in document")


class ExtractTOCResponse(BaseModel):
    """Response containing extracted TOC."""

    toc_entries: list[dict[str, Any]] = Field(
        ...,
        description="List of TOC entries",
    )
    total_entries: int = Field(
        ...,
        description="Total number of entries",
        example=25,
    )
    message: str | None = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "toc_entries": [
                    {"level": 1, "title": "Chapter 1: Introduction", "line": 1},
                    {"level": 2, "title": "1.1 Background", "line": 15},
                    {"level": 2, "title": "1.2 Overview", "line": 45},
                ],
                "total_entries": 3,
            }
        }


class ExtractTitlesRequest(BaseModel):
    """Request to extract titles."""

    file_path: str = Field(
        ...,
        description="Path to the markdown file",
        example="/output/cognitive_psychology.md",
    )


class ExtractTitlesResponse(BaseModel):
    """Response containing extracted titles."""

    titles: list[dict[str, Any]] = Field(
        ...,
        description="List of extracted titles",
    )
    total_count: int = Field(
        ...,
        description="Total number of titles",
        example=50,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "titles": [
                    {"level": 1, "title": "Introduction", "original_line": 1},
                    {"level": 2, "title": "Background", "original_line": 15},
                ],
                "total_count": 2,
            }
        }


class SuggestChangesRequest(BaseModel):
    """Request to suggest heading changes."""

    file_path: str = Field(
        ...,
        description="Path to the markdown file",
        example="/output/cognitive_psychology.md",
    )
    style_guide: str | None = Field(
        default=None,
        description="Optional style guide to follow",
        example="APA 7th edition",
    )


class HeadingChange(BaseModel):
    """A suggested heading change."""

    original: str = Field(..., description="Original heading text")
    suggested: str = Field(..., description="Suggested replacement")
    reason: str = Field(..., description="Reason for the suggestion")
    line: int = Field(..., description="Line number")


class SuggestChangesResponse(BaseModel):
    """Response containing suggested changes."""

    suggestions: list[dict[str, Any]] = Field(
        ...,
        description="List of suggested changes",
    )
    total_suggestions: int = Field(
        ...,
        description="Total number of suggestions",
        example=10,
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence score",
        example=0.85,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": [
                    {
                        "original": "CHAPTER 1",
                        "suggested": "Chapter 1: Introduction",
                        "reason": "Normalize capitalization and add descriptive title",
                        "line": 1,
                    }
                ],
                "total_suggestions": 1,
                "confidence": 0.85,
            }
        }


class ChangeToApply(BaseModel):
    """A change to apply."""

    line: int = Field(..., description="Line number")
    original: str = Field(..., description="Original text")
    replacement: str = Field(..., description="Replacement text")


class ApplyChangesRequest(BaseModel):
    """Request to apply heading changes."""

    file_path: str = Field(
        ...,
        description="Path to the markdown file",
        example="/output/cognitive_psychology.md",
    )
    changes: list[ChangeToApply] = Field(
        ...,
        description="List of changes to apply",
    )
    create_backup: bool = Field(
        default=True,
        description="Whether to create a backup before modifying",
        example=True,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/output/cognitive_psychology.md",
                "changes": [
                    {"line": 1, "original": "CHAPTER 1", "replacement": "Chapter 1: Introduction"},
                ],
                "create_backup": True,
            }
        }


class ApplyChangesResponse(BaseModel):
    """Response for applied changes."""

    success: bool = Field(
        ...,
        description="Whether changes were applied successfully",
        example=True,
    )
    changes_applied: int = Field(
        ...,
        description="Number of changes applied",
        example=5,
    )
    backup_path: str | None = Field(
        default=None,
        description="Path to backup file",
        example="/output/backup/cognitive_psychology_backup.md",
    )
    message: str | None = Field(default=None)


