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


# Work-based sanitization schemas

class WorkListItem(BaseModel):
    """A work item in the list."""

    id: int = Field(..., description="Work ID")
    title: str = Field(..., description="Work title")
    authors: str | None = Field(None, description="Work authors")
    year: int | None = Field(None, description="Publication year")
    work_type: str | None = Field(None, description="Type of work (book, article, etc.)")
    has_sanitized: bool = Field(..., description="Whether sanitized file exists")
    has_original_markdown: bool = Field(..., description="Whether original markdown exists")


class WorkListResponse(BaseModel):
    """Response containing list of works."""

    works: list[WorkListItem] = Field(..., description="List of works")
    total: int = Field(..., description="Total number of works")
    needs_sanitization: int = Field(..., description="Number of works needing sanitization")


class FileStatusInfo(BaseModel):
    """File status information with hash validation."""

    exists: bool = Field(..., description="Whether the file exists in files metadata")
    path: str | None = Field(None, description="File path")
    hash: str | None = Field(None, description="Stored file hash")
    hash_match: bool | None = Field(None, description="Whether current hash matches stored hash (null if file doesn't exist)")
    error: str | None = Field(None, description="Error message if any")


class WorkDetailResponse(BaseModel):
    """Detailed work information for sanitization."""

    id: int = Field(..., description="Work ID")
    title: str = Field(..., description="Work title")
    authors: str | None = Field(None, description="Work authors")
    year: int | None = Field(None, description="Publication year")
    work_type: str | None = Field(None, description="Type of work")
    
    # File statuses
    original_markdown: FileStatusInfo = Field(..., description="Original markdown file status")
    titles: FileStatusInfo = Field(..., description="Titles file status")
    title_changes: FileStatusInfo = Field(..., description="Title changes file status")
    sanitized: FileStatusInfo = Field(..., description="Sanitized file status")


class ExtractTitlesFromWorkRequest(BaseModel):
    """Request to extract titles from a work."""

    source_key: str = Field(
        default="original_markdown",
        description="Source file key (original_markdown or sanitized)",
        example="original_markdown"
    )
    force: bool = Field(
        default=False,
        description="Skip hash validation if True"
    )


class ExtractTitlesFromWorkResponse(BaseModel):
    """Response after extracting titles."""

    success: bool = Field(..., description="Whether extraction succeeded")
    output_path: str = Field(..., description="Path to created titles file")
    message: str | None = Field(None, description="Success or error message")


class SuggestTitleChangesRequest(BaseModel):
    """Request to suggest title changes for a work."""

    source_key: str = Field(
        default="original_markdown",
        description="Source file key (original_markdown or sanitized)",
        example="original_markdown"
    )
    use_full_model: bool = Field(
        default=False,
        description="Use full model tier instead of light"
    )
    force: bool = Field(
        default=False,
        description="Skip hash validation if True"
    )


class SuggestTitleChangesResponse(BaseModel):
    """Response after suggesting title changes."""

    success: bool = Field(..., description="Whether suggestion succeeded")
    output_path: str = Field(..., description="Path to created title_changes file")
    message: str | None = Field(None, description="Success or error message")


class ApplyTitleChangesRequest(BaseModel):
    """Request to apply title changes to a work."""

    source_key: str = Field(
        default="original_markdown",
        description="Source file key (original_markdown or sanitized)",
        example="original_markdown"
    )
    force: bool = Field(
        default=False,
        description="Skip hash validation if True"
    )


class ApplyTitleChangesResponse(BaseModel):
    """Response after applying title changes."""

    success: bool = Field(..., description="Whether application succeeded")
    output_path: str = Field(..., description="Path to created sanitized file")
    message: str | None = Field(None, description="Success or error message")


class SkipApplyRequest(BaseModel):
    """Request to skip sanitization and copy original."""

    source_key: str = Field(
        default="original_markdown",
        description="Source file key (original_markdown or sanitized)",
        example="original_markdown"
    )
    force: bool = Field(
        default=False,
        description="Skip validation and overwrite if sanitized exists"
    )


class SkipApplyResponse(BaseModel):
    """Response after skipping sanitization."""

    success: bool = Field(..., description="Whether copy succeeded")
    output_path: str = Field(..., description="Path to created sanitized file")
    message: str | None = Field(None, description="Success or error message")


class TitlesContentResponse(BaseModel):
    """Response containing titles file content."""

    content: str = Field(..., description="Raw markdown content of titles file")
    filename: str = Field(..., description="Name of the titles file")
    hash: str = Field(..., description="Current hash of the file")


class UpdateTitlesContentRequest(BaseModel):
    """Request to update titles file content."""

    content: str = Field(..., description="New content for the titles file")


class PromptForWorkResponse(BaseModel):
    """Response containing LLM prompt for title changes."""

    prompt: str = Field(..., description="The LLM prompt text")
    work_title: str = Field(..., description="Title of the work")
    work_authors: str = Field(..., description="Authors of the work")


class ManualTitleChangesRequest(BaseModel):
    """Request to save manually generated title changes."""

    llm_response: str = Field(..., description="Raw response text from manual LLM execution")
    source_key: str = Field(
        default="original_markdown",
        description="Source file key (original_markdown or sanitized)"
    )
    force: bool = Field(
        default=False,
        description="Skip validation and overwrite existing files"
    )


class ManualTitleChangesResponse(BaseModel):
    """Response after saving manual title changes."""

    success: bool = Field(..., description="Whether save succeeded")
    output_path: str = Field(..., description="Path to created title_changes file")
    message: str | None = Field(None, description="Success or error message")


class VerifyTitleChangesRequest(BaseModel):
    """Request to verify title changes integrity."""

    source_key: str = Field(
        default="original_markdown",
        description="Source file key (original_markdown or sanitized)"
    )


class VerifyTitleChangesResponse(BaseModel):
    """Response after verifying title changes."""

    success: bool = Field(..., description="Whether validation passed")
    message: str = Field(..., description="Success or error message")
    errors: list[str] = Field(default_factory=list, description="List of validation errors if any")


class TitleChangesContentResponse(BaseModel):
    """Response containing title changes file content."""

    content: str = Field(..., description="Raw markdown content of title_changes file")
    filename: str = Field(..., description="Name of the title_changes file")
    hash: str = Field(..., description="Current hash of the file")


class UpdateTitleChangesContentRequest(BaseModel):
    """Request to update title changes file content."""

    content: str = Field(..., description="New content for the title_changes file")


class AddSanitizedMarkdownRequest(BaseModel):
    """Request to add a new work with sanitized markdown content directly."""

    title: str = Field(
        ...,
        description="Title of the work",
        example="Cognitive Psychology: A Student's Handbook"
    )
    authors: str | None = Field(
        None,
        description="Author(s) of the work",
        example="Michael W. Eysenck, Mark T. Keane"
    )
    year: int | None = Field(
        None,
        ge=1000,
        le=9999,
        description="Year of publication",
        example=2020
    )
    publisher: str | None = Field(
        None,
        description="Publisher name",
        example="Psychology Press"
    )
    isbn: str | None = Field(
        None,
        description="ISBN for books",
        example="978-1138482210"
    )
    edition: str | None = Field(
        None,
        description="Edition information",
        example="8th Edition"
    )
    filename: str = Field(
        ...,
        description="Desired filename for the sanitized markdown (without extension)",
        example="cognitive_psychology"
    )
    content: str = Field(
        ...,
        description="Sanitized markdown content",
        example="# Chapter 1: Introduction\n\nThis is the introduction..."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Cognitive Psychology: A Student's Handbook",
                "authors": "Michael W. Eysenck, Mark T. Keane",
                "year": 2020,
                "publisher": "Psychology Press",
                "isbn": "978-1138482210",
                "edition": "8th Edition",
                "filename": "cognitive_psychology",
                "content": "# Chapter 1: Introduction\n\nThis is the introduction..."
            }
        }


class AddSanitizedMarkdownResponse(BaseModel):
    """Response after adding sanitized markdown."""

    success: bool = Field(..., description="Whether the operation succeeded")
    work_id: int = Field(..., description="ID of the created work")
    output_path: str = Field(..., description="Path to the created sanitized file")
    message: str | None = Field(None, description="Success or error message")


# Interactive title changes table schemas

class HeadingRow(BaseModel):
    """A single row in the heading changes table."""

    line_num: int = Field(..., description="Line number in markdown file")
    original_heading: str = Field(..., description="Original heading level (H1-H6)")
    original_title: str = Field(..., description="Original title text")
    suggested_action: str = Field(..., description="Suggested action (H1-H6 or REMOVE)")
    suggested_title: str = Field(..., description="Suggested title text")

    class Config:
        json_schema_extra = {
            "example": {
                "line_num": 157,
                "original_heading": "H2",
                "original_title": "Cognitive Psychology and the Brain",
                "suggested_action": "H1",
                "suggested_title": "1 Cognitive Psychology and the Brain"
            }
        }


class HeadingTableResponse(BaseModel):
    """Response containing table data for title changes."""

    work_id: int = Field(..., description="Work ID")
    source_file: str = Field(..., description="Relative path to source markdown")
    rows: list[HeadingRow] = Field(..., description="All heading rows merged with changes")
    filename: str = Field(..., description="Title changes filename")
    hash: str = Field(..., description="Current hash of title_changes file")

    class Config:
        json_schema_extra = {
            "example": {
                "work_id": 1,
                "source_file": "./test3.md",
                "rows": [
                    {
                        "line_num": 157,
                        "original_heading": "H2",
                        "original_title": "Cognitive Psychology and the Brain",
                        "suggested_action": "H1",
                        "suggested_title": "1 Cognitive Psychology and the Brain"
                    }
                ],
                "filename": "test3.title_changes.md",
                "hash": "abc123def456..."
            }
        }


class UpdateHeadingTableRequest(BaseModel):
    """Request to update title changes from table data."""

    rows: list[HeadingRow] = Field(..., description="Updated heading rows")

    class Config:
        json_schema_extra = {
            "example": {
                "rows": [
                    {
                        "line_num": 157,
                        "original_heading": "H2",
                        "original_title": "Cognitive Psychology and the Brain",
                        "suggested_action": "H1",
                        "suggested_title": "1 Cognitive Psychology and the Brain"
                    }
                ]
            }
        }


