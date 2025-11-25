"""
Settings Router - Configuration and settings management.

Endpoints:
    GET  /settings/         - Get all current settings
    GET  /settings/{key}    - Get a specific setting
    PUT  /settings/{key}    - Update a specific setting
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Path, status

from psychrag_api.schemas.settings import (
    AllSettingsResponse,
    SettingResponse,
    SettingUpdateRequest,
)

router = APIRouter()


@router.get(
    "/",
    response_model=AllSettingsResponse,
    summary="Get all settings",
    description="Retrieve all current system settings and their values.",
    responses={
        200: {
            "description": "Settings retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "settings": {
                            "embedding_model": "text-embedding-3-small",
                            "llm_model": "gpt-4",
                            "chunk_size": 512,
                            "chunk_overlap": 50,
                        }
                    }
                }
            },
        }
    },
)
async def get_all_settings() -> AllSettingsResponse:
    """
    Get all system settings.
    
    Returns configuration values for:
    - Embedding models
    - LLM models
    - Chunking parameters
    - Database settings
    """
    # TODO: Implement using psychrag.ai.config
    return AllSettingsResponse(
        settings={
            "embedding_model": "text-embedding-3-small",
            "llm_model": "gpt-4o",
            "chunk_size": 512,
            "chunk_overlap": 50,
            "database_url": "postgresql://...",
        }
    )


@router.get(
    "/{key}",
    response_model=SettingResponse,
    summary="Get specific setting",
    description="Retrieve a specific setting by its key.",
    responses={
        200: {"description": "Setting retrieved successfully"},
        404: {"description": "Setting not found"},
    },
)
async def get_setting(
    key: str = Path(
        ...,
        description="The setting key to retrieve",
        example="embedding_model",
    ),
) -> SettingResponse:
    """Get a specific setting by key."""
    # TODO: Implement actual setting retrieval
    valid_keys = ["embedding_model", "llm_model", "chunk_size", "chunk_overlap"]
    
    if key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found",
        )
    
    mock_values: dict[str, Any] = {
        "embedding_model": "text-embedding-3-small",
        "llm_model": "gpt-4o",
        "chunk_size": 512,
        "chunk_overlap": 50,
    }
    
    return SettingResponse(
        key=key,
        value=mock_values.get(key),
        description=f"Configuration for {key}",
    )


@router.put(
    "/{key}",
    response_model=SettingResponse,
    summary="Update setting",
    description="Update a specific setting value.",
    responses={
        200: {"description": "Setting updated successfully"},
        404: {"description": "Setting not found"},
        422: {"description": "Invalid value for setting"},
    },
)
async def update_setting(
    request: SettingUpdateRequest,
    key: str = Path(
        ...,
        description="The setting key to update",
        example="chunk_size",
    ),
) -> SettingResponse:
    """
    Update a setting value.
    
    Some settings may require a restart to take effect.
    """
    # TODO: Implement actual setting update
    return SettingResponse(
        key=key,
        value=request.value,
        description=f"Updated {key} successfully (stub)",
    )


