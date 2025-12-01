# T03: RAG Config API endpoints with validation

## Context

- **PRD**: [prd-rag-settings.md](prd-rag-settings.md)
- **PRD Sections**: Technical Specification → API Endpoints (lines 173-249)
- **User value**: Exposes RAG configuration management via REST API, enabling the frontend to create, read, update, and delete configuration presets with robust validation.

## Outcome

When this ticket is done:
- REST API provides 7 endpoints for complete CRUD operations on RAG config presets
- All endpoints validate input using Pydantic schemas with parameter constraints
- API enforces business rules (single default, cannot delete default without replacement)
- Frontend can call API to manage presets: list, get, create, update, set default, delete
- All endpoints include proper error handling with meaningful HTTP status codes

## Scope

### In scope:
- Create Pydantic schemas in `src/psychrag_api/schemas/rag_config.py` with:
  - Request schemas: `RagConfigCreate`, `RagConfigUpdate`
  - Response schema: `RagConfigResponse`
  - Parameter validation schemas with min/max constraints
- Create API router `src/psychrag_api/routers/rag_config.py` with 7 endpoints:
  - `GET /api/rag-config/` - List all presets
  - `GET /api/rag-config/default` - Get default preset
  - `GET /api/rag-config/{preset_name}` - Get specific preset
  - `POST /api/rag-config/` - Create new preset
  - `PUT /api/rag-config/{preset_name}` - Update preset
  - `PUT /api/rag-config/{preset_name}/set-default` - Set as default
  - `DELETE /api/rag-config/{preset_name}` - Delete preset
- Register router in `src/psychrag_api/main.py`
- Unit tests for all endpoints

### Out of scope:
- Frontend UI (T05)
- Integration into RAG pipeline modules (T04)
- Authentication/authorization (future enhancement)
- Config versioning/history (future enhancement)

## Implementation plan

### Backend - Pydantic Schemas

**File**: `src/psychrag_api/schemas/rag_config.py`

1. **Create comprehensive validation schemas**:

```python
"""
Pydantic schemas for RAG configuration API.

Defines request/response models with validation for RAG config presets.
Validation ensures parameters are within acceptable ranges per PRD specs.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Parameter Schemas with Validation
# ============================================================================

class RetrievalParams(BaseModel):
    """Retrieval stage parameters with validation constraints."""

    dense_limit: int = Field(19, ge=1, le=100, description="Max results per dense vector query")
    lexical_limit: int = Field(5, ge=1, le=50, description="Max results per lexical (BM25) query")
    rrf_k: int = Field(50, ge=1, le=100, description="RRF constant for rank fusion")
    top_k_rrf: int = Field(75, ge=1, le=200, description="Top candidates after RRF fusion")
    top_n_final: int = Field(17, ge=1, le=50, description="Final number of results after MMR")
    entity_boost: float = Field(0.05, ge=0.0, le=0.5, description="Score boost per entity match")
    min_word_count: int = Field(150, ge=0, le=1000, description="Minimum words in chunk (0 to disable)")
    min_char_count: int = Field(250, ge=0, le=5000, description="Minimum characters in chunk (0 to disable)")
    min_content_length: int = Field(750, ge=0, le=5000, description="Min content length before enrichment")
    enrich_lines_above: int = Field(0, ge=0, le=50, description="Lines to add above chunk when enriching")
    enrich_lines_below: int = Field(13, ge=0, le=50, description="Lines to add below chunk when enriching")
    mmr_lambda: float = Field(0.7, ge=0.0, le=1.0, description="MMR balance: relevance (1.0) vs diversity (0.0)")
    reranker_batch_size: int = Field(8, ge=1, le=32, description="Batch size for BGE reranker inference")
    reranker_max_length: int = Field(512, ge=128, le=1024, description="Max token length for reranker")

    @model_validator(mode='after')
    def validate_top_k_consistency(self):
        """Ensure top_k_rrf >= top_n_final."""
        if self.top_k_rrf < self.top_n_final:
            raise ValueError("top_k_rrf must be >= top_n_final")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "dense_limit": 19,
                "lexical_limit": 5,
                "rrf_k": 50,
                "top_k_rrf": 75,
                "top_n_final": 17,
                "entity_boost": 0.05,
                "min_word_count": 150,
                "min_char_count": 250,
                "min_content_length": 750,
                "enrich_lines_above": 0,
                "enrich_lines_below": 13,
                "mmr_lambda": 0.7,
                "reranker_batch_size": 8,
                "reranker_max_length": 512
            }
        }


class ConsolidationParams(BaseModel):
    """Consolidation stage parameters with validation constraints."""

    coverage_threshold: float = Field(0.5, ge=0.0, le=1.0, description="% of parent coverage to replace with parent")
    line_gap: int = Field(7, ge=0, le=50, description="Max lines between chunks to merge them")
    min_content_length: int = Field(350, ge=0, le=5000, description="Min characters for final output inclusion")
    enrich_from_md: bool = Field(True, description="Read content from markdown during consolidation")

    class Config:
        json_schema_extra = {
            "example": {
                "coverage_threshold": 0.5,
                "line_gap": 7,
                "min_content_length": 350,
                "enrich_from_md": True
            }
        }


class AugmentationParams(BaseModel):
    """Augmentation stage parameters with validation constraints."""

    top_n_contexts: int = Field(5, ge=1, le=20, description="Number of top contexts to include in prompt")

    class Config:
        json_schema_extra = {
            "example": {
                "top_n_contexts": 5
            }
        }


class RagConfigParams(BaseModel):
    """Complete RAG configuration parameters (all stages)."""

    retrieval: RetrievalParams
    consolidation: ConsolidationParams
    augmentation: AugmentationParams


# ============================================================================
# Request Schemas
# ============================================================================

class RagConfigCreate(BaseModel):
    """Request schema for creating a new RAG config preset."""

    preset_name: str = Field(..., min_length=1, max_length=100, description="Unique preset name")
    description: Optional[str] = Field(None, description="Optional description of preset purpose")
    is_default: bool = Field(False, description="Set as default preset (will unset other defaults)")
    config: RagConfigParams = Field(..., description="Configuration parameters")

    @field_validator('preset_name')
    @classmethod
    def validate_preset_name(cls, v: str) -> str:
        """Validate preset name: no leading/trailing whitespace, no special chars."""
        v = v.strip()
        if not v:
            raise ValueError("Preset name cannot be empty or whitespace")
        # Allow alphanumeric, spaces, hyphens, underscores
        if not all(c.isalnum() or c in [' ', '-', '_'] for c in v):
            raise ValueError("Preset name can only contain letters, numbers, spaces, hyphens, and underscores")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "preset_name": "Fast Retrieval",
                "description": "Optimized for speed with fewer candidates",
                "is_default": False,
                "config": {
                    "retrieval": {
                        "dense_limit": 10,
                        "lexical_limit": 3,
                        "top_n_final": 10
                    },
                    "consolidation": {"coverage_threshold": 0.5, "line_gap": 7, "min_content_length": 350, "enrich_from_md": True},
                    "augmentation": {"top_n_contexts": 3}
                }
            }
        }


class RagConfigUpdate(BaseModel):
    """Request schema for updating an existing RAG config preset."""

    description: Optional[str] = Field(None, description="Update preset description")
    config: Optional[RagConfigParams] = Field(None, description="Update configuration parameters")

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Updated description",
                "config": {
                    "retrieval": {"dense_limit": 20},
                    "consolidation": {"line_gap": 10},
                    "augmentation": {"top_n_contexts": 7}
                }
            }
        }


# ============================================================================
# Response Schema
# ============================================================================

class RagConfigResponse(BaseModel):
    """Response schema for RAG config preset."""

    id: int
    preset_name: str
    is_default: bool
    description: Optional[str]
    config: RagConfigParams
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "preset_name": "Default",
                "is_default": True,
                "description": "Default balanced configuration",
                "config": {
                    "retrieval": {"dense_limit": 19, "lexical_limit": 5},
                    "consolidation": {"coverage_threshold": 0.5, "line_gap": 7},
                    "augmentation": {"top_n_contexts": 5}
                },
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }
```

### Backend - API Router

**File**: `src/psychrag_api/routers/rag_config.py`

2. **Create router with all 7 endpoints**:

```python
"""
RAG Config Router - Configuration preset management.

Endpoints for managing RAG pipeline configuration presets.

Endpoints:
    GET    /api/rag-config/                    - List all presets
    GET    /api/rag-config/default             - Get default preset
    GET    /api/rag-config/{preset_name}       - Get specific preset
    POST   /api/rag-config/                    - Create new preset
    PUT    /api/rag-config/{preset_name}       - Update preset
    PUT    /api/rag-config/{preset_name}/set-default - Set as default
    DELETE /api/rag-config/{preset_name}       - Delete preset
"""

from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from psychrag.data.database import get_session
from psychrag.data.models.rag_config import RagConfig
from psychrag_api.schemas.rag_config import (
    RagConfigCreate,
    RagConfigUpdate,
    RagConfigResponse,
)

router = APIRouter()


# ============================================================================
# GET Endpoints
# ============================================================================

@router.get(
    "/",
    response_model=List[RagConfigResponse],
    summary="List all RAG config presets",
    description="Get a list of all available RAG configuration presets.",
)
async def list_presets() -> List[RagConfigResponse]:
    """List all RAG config presets."""
    try:
        with get_session() as session:
            presets = session.query(RagConfig).order_by(
                RagConfig.is_default.desc(),  # Default first
                RagConfig.preset_name
            ).all()
            return [RagConfigResponse.model_validate(preset) for preset in presets]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list presets: {str(e)}"
        )


@router.get(
    "/default",
    response_model=RagConfigResponse,
    summary="Get default preset",
    description="Get the RAG configuration preset marked as default.",
)
async def get_default_preset() -> RagConfigResponse:
    """Get default RAG config preset."""
    try:
        with get_session() as session:
            preset = session.query(RagConfig).filter(RagConfig.is_default == True).first()
            if not preset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No default preset found. Database may not be initialized."
                )
            return RagConfigResponse.model_validate(preset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get default preset: {str(e)}"
        )


@router.get(
    "/{preset_name}",
    response_model=RagConfigResponse,
    summary="Get preset by name",
    description="Get a specific RAG configuration preset by name.",
)
async def get_preset_by_name(preset_name: str) -> RagConfigResponse:
    """Get RAG config preset by name."""
    try:
        with get_session() as session:
            preset = session.query(RagConfig).filter(
                RagConfig.preset_name == preset_name
            ).first()
            if not preset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Preset '{preset_name}' not found"
                )
            return RagConfigResponse.model_validate(preset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preset: {str(e)}"
        )


# ============================================================================
# POST Endpoint
# ============================================================================

@router.post(
    "/",
    response_model=RagConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new preset",
    description="Create a new RAG configuration preset.",
)
async def create_preset(preset_data: RagConfigCreate) -> RagConfigResponse:
    """Create new RAG config preset."""
    try:
        with get_session() as session:
            # Check for duplicate name
            existing = session.query(RagConfig).filter(
                RagConfig.preset_name == preset_data.preset_name
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Preset '{preset_data.preset_name}' already exists"
                )

            # Create new preset
            new_preset = RagConfig(
                preset_name=preset_data.preset_name,
                is_default=preset_data.is_default,
                description=preset_data.description,
                config=preset_data.config.model_dump()
            )
            session.add(new_preset)
            session.commit()
            session.refresh(new_preset)

            return RagConfigResponse.model_validate(new_preset)

    except HTTPException:
        raise
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Preset name already exists: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create preset: {str(e)}"
        )


# ============================================================================
# PUT Endpoints
# ============================================================================

@router.put(
    "/{preset_name}",
    response_model=RagConfigResponse,
    summary="Update preset",
    description="Update an existing RAG configuration preset.",
)
async def update_preset(preset_name: str, update_data: RagConfigUpdate) -> RagConfigResponse:
    """Update RAG config preset."""
    try:
        with get_session() as session:
            preset = session.query(RagConfig).filter(
                RagConfig.preset_name == preset_name
            ).first()
            if not preset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Preset '{preset_name}' not found"
                )

            # Update fields
            if update_data.description is not None:
                preset.description = update_data.description
            if update_data.config is not None:
                preset.config = update_data.config.model_dump()

            session.commit()
            session.refresh(preset)

            return RagConfigResponse.model_validate(preset)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preset: {str(e)}"
        )


@router.put(
    "/{preset_name}/set-default",
    response_model=RagConfigResponse,
    summary="Set preset as default",
    description="Mark a preset as the default configuration. Unsets any other default.",
)
async def set_default_preset(preset_name: str) -> RagConfigResponse:
    """Set preset as default."""
    try:
        with get_session() as session:
            preset = session.query(RagConfig).filter(
                RagConfig.preset_name == preset_name
            ).first()
            if not preset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Preset '{preset_name}' not found"
                )

            # Set as default (trigger will handle unsetting others)
            preset.is_default = True
            session.commit()
            session.refresh(preset)

            return RagConfigResponse.model_validate(preset)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set default: {str(e)}"
        )


# ============================================================================
# DELETE Endpoint
# ============================================================================

@router.delete(
    "/{preset_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete preset",
    description="Delete a RAG configuration preset. Cannot delete the default preset.",
)
async def delete_preset(preset_name: str):
    """Delete RAG config preset."""
    try:
        with get_session() as session:
            preset = session.query(RagConfig).filter(
                RagConfig.preset_name == preset_name
            ).first()
            if not preset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Preset '{preset_name}' not found"
                )

            # Prevent deleting default preset
            if preset.is_default:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete default preset. Set another preset as default first."
                )

            session.delete(preset)
            session.commit()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete preset: {str(e)}"
        )
```

### Backend - Router Registration

**File**: `src/psychrag_api/main.py`

3. **Register router** in main FastAPI app (add after existing router imports around line 32):

```python
from psychrag_api.routers import (
    chunking,
    conversion,
    corpus,
    init,
    rag,
    rag_config,  # Add this import
    sanitization,
    settings,
    templates,
    vectorization,
)
```

4. **Add OpenAPI tag** (add to `openapi_tags` list around line 96):

```python
{
    "name": "RAG Config",
    "description": "RAG configuration preset management. Create, edit, and manage retrieval/consolidation/augmentation settings.",
},
```

5. **Include router** (add after other `app.include_router` calls around line 135):

```python
app.include_router(rag_config.router, prefix="/api/rag-config", tags=["RAG Config"])
```

## Unit tests

**File**: `tests/unit/test_rag_config_api.py`

Create comprehensive API tests:

```python
"""
Unit tests for RAG Config API endpoints.

Tests all CRUD operations and validation.
"""

import pytest
from fastapi.testclient import TestClient

from psychrag_api.main import app
from psychrag.data.database import get_session
from psychrag.data.models.rag_config import RagConfig

client = TestClient(app)


class TestListPresets:
    """Test GET /api/rag-config/ endpoint."""

    def test_list_presets_success(self):
        """Test successful listing of all presets."""
        response = client.get("/api/rag-config/")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("preset_name" in item for item in data)

    def test_list_presets_default_first(self):
        """Test that default preset appears first in list."""
        response = client.get("/api/rag-config/")
        data = response.json()

        # First item should be default
        assert data[0]["is_default"] is True


class TestGetDefaultPreset:
    """Test GET /api/rag-config/default endpoint."""

    def test_get_default_success(self):
        """Test successful retrieval of default preset."""
        response = client.get("/api/rag-config/default")
        assert response.status_code == 200

        data = response.json()
        assert data["is_default"] is True
        assert "config" in data
        assert "retrieval" in data["config"]


class TestGetPresetByName:
    """Test GET /api/rag-config/{preset_name} endpoint."""

    def test_get_preset_by_name_success(self):
        """Test successful retrieval by name."""
        response = client.get("/api/rag-config/Default")
        assert response.status_code == 200

        data = response.json()
        assert data["preset_name"] == "Default"

    def test_get_preset_by_name_not_found(self):
        """Test 404 for non-existent preset."""
        response = client.get("/api/rag-config/NonExistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreatePreset:
    """Test POST /api/rag-config/ endpoint."""

    def test_create_preset_success(self):
        """Test successful preset creation."""
        payload = {
            "preset_name": "TestCreate",
            "description": "Test preset",
            "is_default": False,
            "config": {
                "retrieval": {
                    "dense_limit": 10,
                    "lexical_limit": 5,
                    "rrf_k": 50,
                    "top_k_rrf": 75,
                    "top_n_final": 17,
                    "entity_boost": 0.05,
                    "min_word_count": 150,
                    "min_char_count": 250,
                    "min_content_length": 750,
                    "enrich_lines_above": 0,
                    "enrich_lines_below": 13,
                    "mmr_lambda": 0.7,
                    "reranker_batch_size": 8,
                    "reranker_max_length": 512
                },
                "consolidation": {
                    "coverage_threshold": 0.5,
                    "line_gap": 7,
                    "min_content_length": 350,
                    "enrich_from_md": True
                },
                "augmentation": {
                    "top_n_contexts": 5
                }
            }
        }

        response = client.post("/api/rag-config/", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["preset_name"] == "TestCreate"
        assert data["config"]["retrieval"]["dense_limit"] == 10

        # Cleanup
        client.delete("/api/rag-config/TestCreate")

    def test_create_preset_duplicate_name(self):
        """Test 409 conflict for duplicate name."""
        payload = {
            "preset_name": "Default",  # Existing preset
            "is_default": False,
            "config": {
                "retrieval": {},
                "consolidation": {},
                "augmentation": {}
            }
        }

        response = client.post("/api/rag-config/", json=payload)
        assert response.status_code == 409

    def test_create_preset_validation_error(self):
        """Test validation errors for invalid parameters."""
        payload = {
            "preset_name": "InvalidParams",
            "is_default": False,
            "config": {
                "retrieval": {
                    "dense_limit": 999  # Exceeds max of 100
                },
                "consolidation": {},
                "augmentation": {}
            }
        }

        response = client.post("/api/rag-config/", json=payload)
        assert response.status_code == 422  # Validation error


class TestUpdatePreset:
    """Test PUT /api/rag-config/{preset_name} endpoint."""

    @pytest.fixture(autouse=True)
    def setup_test_preset(self):
        """Create test preset for update tests."""
        payload = {
            "preset_name": "TestUpdate",
            "is_default": False,
            "config": {
                "retrieval": {"dense_limit": 15},
                "consolidation": {"line_gap": 5},
                "augmentation": {"top_n_contexts": 3}
            }
        }
        client.post("/api/rag-config/", json=payload)
        yield
        client.delete("/api/rag-config/TestUpdate")

    def test_update_preset_description(self):
        """Test updating preset description."""
        update_payload = {
            "description": "Updated description"
        }

        response = client.put("/api/rag-config/TestUpdate", json=update_payload)
        assert response.status_code == 200

        data = response.json()
        assert data["description"] == "Updated description"

    def test_update_preset_config(self):
        """Test updating preset config."""
        update_payload = {
            "config": {
                "retrieval": {"dense_limit": 25},
                "consolidation": {"line_gap": 10},
                "augmentation": {"top_n_contexts": 7}
            }
        }

        response = client.put("/api/rag-config/TestUpdate", json=update_payload)
        assert response.status_code == 200

        data = response.json()
        assert data["config"]["retrieval"]["dense_limit"] == 25


class TestSetDefaultPreset:
    """Test PUT /api/rag-config/{preset_name}/set-default endpoint."""

    @pytest.fixture(autouse=True)
    def setup_test_preset(self):
        """Create test preset."""
        payload = {
            "preset_name": "TestDefault",
            "is_default": False,
            "config": {
                "retrieval": {},
                "consolidation": {},
                "augmentation": {}
            }
        }
        client.post("/api/rag-config/", json=payload)
        yield
        # Reset default back
        client.put("/api/rag-config/Default/set-default")
        client.delete("/api/rag-config/TestDefault")

    def test_set_default_success(self):
        """Test setting preset as default."""
        response = client.put("/api/rag-config/TestDefault/set-default")
        assert response.status_code == 200

        data = response.json()
        assert data["is_default"] is True

        # Verify old default is now false
        default_response = client.get("/api/rag-config/default")
        assert default_response.json()["preset_name"] == "TestDefault"


class TestDeletePreset:
    """Test DELETE /api/rag-config/{preset_name} endpoint."""

    def test_delete_preset_success(self):
        """Test successful preset deletion."""
        # Create preset to delete
        payload = {
            "preset_name": "TestDelete",
            "is_default": False,
            "config": {
                "retrieval": {},
                "consolidation": {},
                "augmentation": {}
            }
        }
        client.post("/api/rag-config/", json=payload)

        # Delete it
        response = client.delete("/api/rag-config/TestDelete")
        assert response.status_code == 204

        # Verify deleted
        get_response = client.get("/api/rag-config/TestDelete")
        assert get_response.status_code == 404

    def test_delete_default_preset_fails(self):
        """Test that deleting default preset is prevented."""
        response = client.delete("/api/rag-config/Default")
        assert response.status_code == 400
        assert "Cannot delete default" in response.json()["detail"]

    def test_delete_nonexistent_preset(self):
        """Test 404 for deleting non-existent preset."""
        response = client.delete("/api/rag-config/NonExistent")
        assert response.status_code == 404
```

**Test execution**:
```bash
venv\Scripts\pytest tests/unit/test_rag_config_api.py -v
```

## Manual test plan

### Setup:
1. Start API server: `venv\Scripts\uvicorn psychrag_api.main:app --reload`
2. Open Swagger UI: http://localhost:8000/docs

### Test scenarios:

**1. List all presets**
- Navigate to `GET /api/rag-config/`
- Execute → Should return array with at least Default preset

**2. Get default preset**
- Navigate to `GET /api/rag-config/default`
- Execute → Should return Default preset with is_default=true

**3. Create new preset**
- Navigate to `POST /api/rag-config/`
- Use example payload, change preset_name to "Fast"
- Execute → Should return 201 with created preset

**4. Get specific preset**
- Navigate to `GET /api/rag-config/{preset_name}`
- Enter "Fast" as preset_name
- Execute → Should return the Fast preset

**5. Update preset**
- Navigate to `PUT /api/rag-config/{preset_name}`
- Enter "Fast" as preset_name
- Update description: "Optimized for speed"
- Execute → Should return 200 with updated preset

**6. Set as default**
- Navigate to `PUT /api/rag-config/{preset_name}/set-default`
- Enter "Fast" as preset_name
- Execute → Should return 200, is_default=true

**7. Delete preset**
- Create another preset "Temporary"
- Navigate to `DELETE /api/rag-config/{preset_name}`
- Enter "Temporary" as preset_name
- Execute → Should return 204

**8. Error cases**
- Try to delete default preset → Should return 400
- Try to create duplicate name → Should return 409
- Try to get non-existent preset → Should return 404

## Dependencies and sequencing

### Dependencies:
- **Requires**: T01 (database), T02 (model and loader)
- **Blocks**: T05 (frontend needs API)

### Sequencing notes:
- Can start after T02 is complete
- T04 (integration) can be developed in parallel once T02 is done
- This is on the critical path for T05 (UI)

## Clarifications and assumptions

### Assumptions:
1. **Validation**: Using Pydantic Field constraints per PRD parameter specs
2. **Error handling**: Using standard HTTP status codes (200, 201, 204, 400, 404, 409, 422, 500)
3. **Default handling**: Database trigger handles single default constraint
4. **DELETE safety**: Cannot delete default preset without setting another first
5. **Preset names**: Case-sensitive, allow alphanumeric + spaces/hyphens/underscores
6. **Response format**: Always return full `RagConfigResponse` with all fields

### Open questions (non-blocking):
1. Should we add batch operations (e.g., delete multiple presets)?
2. Should we add a PATCH endpoint for partial updates vs. PUT?
3. Should we add preset duplication endpoint (copy existing preset)?
4. Should we add preset import/export (JSON file upload/download)?

### Implementer notes:

> **Before implementing**:
> - Review existing routers (`settings.py`, `templates.py`) to match code style
> - Ensure T01 and T02 are complete and tested
> - Review FastAPI best practices for error handling

> **During implementation**:
> - Test each endpoint individually in Swagger UI as you write it
> - Ensure validation error messages are user-friendly
> - Use proper HTTP status codes (don't return 500 for business logic errors)
> - Handle database session cleanup properly (use context manager)

> **After implementation**:
> - Run all unit tests and verify 100% pass
> - Test all endpoints manually via Swagger UI
> - Verify error messages are helpful
> - Check API documentation in Swagger UI is clear
> - Test edge cases: empty description, min/max parameter values
