"""
Pydantic schemas for Chunking router.
"""

from typing import Any

from pydantic import BaseModel, Field


class ChunkByHeadingsRequest(BaseModel):
    """Request to chunk by headings."""

    file_path: str = Field(
        ...,
        description="Path to the markdown file",
        example="/output/cognitive_psychology.md",
    )
    min_level: int = Field(
        default=1,
        ge=1,
        le=6,
        description="Minimum heading level to chunk at",
        example=2,
    )
    max_level: int = Field(
        default=3,
        ge=1,
        le=6,
        description="Maximum heading level to chunk at",
        example=3,
    )
    include_parent_context: bool = Field(
        default=True,
        description="Include parent heading context in chunks",
        example=True,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/output/cognitive_psychology.md",
                "min_level": 2,
                "max_level": 3,
                "include_parent_context": True,
            }
        }


class ChunkByContentRequest(BaseModel):
    """Request to chunk by content size."""

    file_path: str = Field(
        ...,
        description="Path to the markdown file",
        example="/output/cognitive_psychology.md",
    )
    chunk_size: int = Field(
        default=512,
        ge=100,
        le=8000,
        description="Target chunk size in tokens",
        example=512,
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=500,
        description="Overlap between chunks in tokens",
        example=50,
    )
    respect_paragraphs: bool = Field(
        default=True,
        description="Avoid splitting mid-paragraph",
        example=True,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/output/cognitive_psychology.md",
                "chunk_size": 512,
                "chunk_overlap": 50,
                "respect_paragraphs": True,
            }
        }


class ChunkData(BaseModel):
    """A single chunk of content."""

    id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="Chunk text content")
    heading: str | None = Field(None, description="Section heading")
    level: int | None = Field(None, description="Heading level")
    start_line: int = Field(..., description="Starting line number")
    end_line: int = Field(..., description="Ending line number")
    token_count: int = Field(..., description="Token count")


class ChunkResponse(BaseModel):
    """Response containing chunks."""

    chunks: list[dict[str, Any]] = Field(
        ...,
        description="List of chunks",
    )
    total_chunks: int = Field(
        ...,
        description="Total number of chunks",
        example=45,
    )
    total_tokens: int = Field(
        default=0,
        description="Total token count across all chunks",
        example=23000,
    )
    message: str | None = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "chunks": [
                    {
                        "id": "chunk_001",
                        "content": "Introduction content...",
                        "heading": "Introduction",
                        "level": 1,
                        "start_line": 1,
                        "end_line": 50,
                        "token_count": 450,
                    }
                ],
                "total_chunks": 1,
                "total_tokens": 450,
            }
        }


class SuggestChunksRequest(BaseModel):
    """Request for AI chunk suggestions."""

    file_path: str = Field(
        ...,
        description="Path to the markdown file",
        example="/output/cognitive_psychology.md",
    )
    target_chunk_size: int = Field(
        default=512,
        description="Target chunk size for suggestions",
        example=512,
    )


class ChunkSuggestion(BaseModel):
    """A suggested chunk boundary."""

    start_line: int = Field(..., description="Suggested start line")
    end_line: int = Field(..., description="Suggested end line")
    reason: str = Field(..., description="Reason for this boundary")
    confidence: float = Field(..., description="Confidence score")


class SuggestChunksResponse(BaseModel):
    """Response containing chunk suggestions."""

    suggestions: list[dict[str, Any]] = Field(
        ...,
        description="List of chunk boundary suggestions",
    )
    total_suggestions: int = Field(
        ...,
        description="Total number of suggestions",
        example=25,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": [
                    {
                        "start_line": 1,
                        "end_line": 50,
                        "reason": "Complete introduction section",
                        "confidence": 0.92,
                    }
                ],
                "total_suggestions": 1,
            }
        }


class ExtractBibRequest(BaseModel):
    """Request to extract bibliography."""

    file_path: str = Field(
        ...,
        description="Path to the markdown file",
        example="/output/cognitive_psychology.md",
    )


class BibEntry(BaseModel):
    """A bibliography entry."""

    id: str = Field(..., description="Entry identifier")
    authors: list[str] = Field(..., description="List of authors")
    title: str = Field(..., description="Work title")
    year: int | None = Field(None, description="Publication year")
    journal: str | None = Field(None, description="Journal name")
    raw_text: str = Field(..., description="Original citation text")


class ExtractBibResponse(BaseModel):
    """Response containing bibliography entries."""

    entries: list[dict[str, Any]] = Field(
        ...,
        description="List of bibliography entries",
    )
    total_entries: int = Field(
        ...,
        description="Total number of entries",
        example=150,
    )
    message: str | None = Field(default=None)


class LLMProcessRequest(BaseModel):
    """Request to process chunks with LLM."""

    chunk_ids: list[str] = Field(
        ...,
        description="List of chunk IDs to process",
        example=["chunk_001", "chunk_002"],
    )
    operation: str = Field(
        ...,
        description="Operation to perform: summarize, extract_key_points, generate_questions",
        example="summarize",
    )
    model: str | None = Field(
        default=None,
        description="LLM model to use (defaults to configured model)",
        example="gpt-4o",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_ids": ["chunk_001", "chunk_002", "chunk_003"],
                "operation": "summarize",
                "model": "gpt-4o",
            }
        }


class LLMProcessResponse(BaseModel):
    """Response for LLM processing job."""

    job_id: str = Field(
        ...,
        description="Unique job identifier",
        example="llm_proc_12345",
    )
    status: str = Field(
        ...,
        description="Job status",
        example="queued",
    )
    operation: str = Field(
        ...,
        description="Requested operation",
        example="summarize",
    )
    chunks_queued: int = Field(
        ...,
        description="Number of chunks queued",
        example=3,
    )
    message: str | None = Field(default=None)


