"""
Pydantic schemas for Settings router.
"""

from typing import Any

from pydantic import BaseModel, Field


class SettingResponse(BaseModel):
    """Response for a single setting."""

    key: str = Field(
        ...,
        description="Setting key/name",
        example="embedding_model",
    )
    value: Any = Field(
        ...,
        description="Current setting value",
        example="text-embedding-3-small",
    )
    description: str | None = Field(
        default=None,
        description="Description of what this setting controls",
        example="The embedding model used for vectorization",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "key": "embedding_model",
                "value": "text-embedding-3-small",
                "description": "The embedding model used for vectorization",
            }
        }


class AllSettingsResponse(BaseModel):
    """Response containing all settings."""

    settings: dict[str, Any] = Field(
        ...,
        description="Dictionary of all settings",
        example={
            "embedding_model": "text-embedding-3-small",
            "llm_model": "gpt-4o",
            "chunk_size": 512,
        },
    )

    class Config:
        json_schema_extra = {
            "example": {
                "settings": {
                    "embedding_model": "text-embedding-3-small",
                    "llm_model": "gpt-4o",
                    "chunk_size": 512,
                    "chunk_overlap": 50,
                    "rerank_enabled": True,
                }
            }
        }


class SettingUpdateRequest(BaseModel):
    """Request to update a setting."""

    value: Any = Field(
        ...,
        description="New value for the setting",
        example=1024,
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "summary": "Update chunk size",
                    "value": {"value": 1024},
                },
                {
                    "summary": "Update model",
                    "value": {"value": "gpt-4o-mini"},
                },
                {
                    "summary": "Update boolean",
                    "value": {"value": True},
                },
            ]
        }


