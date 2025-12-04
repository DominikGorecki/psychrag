COMPLETE

# T02: Backend API endpoints for template CRUD operations

## Context

- **PRD**: [templates_prd.md](templates_prd.md)
- **PRD Section**: Lines 3-15 (UI interactions that require API support)
- **User Value**: Provides REST API endpoints for managing prompt templates, enabling the UI to list templates, retrieve versions, update active templates, create new versions, and edit template content.

## Outcome

The FastAPI backend exposes endpoints under `/settings/templates/` that support:
- Listing all templates grouped by function tag with version summaries
- Retrieving a specific template by function tag and version
- Creating a new version for a function tag
- Updating an existing template's content (overwrite)
- Setting the active version for a function tag

These endpoints can be tested independently via Swagger UI or curl before the frontend exists.

## Scope

**In scope:**
- Create new router file `/src/psychrag_api/routers/templates.py`
- Implement 5 REST endpoints:
  1. `GET /settings/templates/` - List all template functions with version summaries
  2. `GET /settings/templates/{function_tag}` - Get all versions for a function tag
  3. `GET /settings/templates/{function_tag}/{version}` - Get specific version
  4. `POST /settings/templates/{function_tag}` - Create new version (auto-increment)
  5. `PUT /settings/templates/{function_tag}/{version}` - Update template content
  6. `PUT /settings/templates/{function_tag}/{version}/activate` - Set as active version
- Create Pydantic schemas in `/src/psychrag_api/schemas/templates.py`
- Add router to main app in `/src/psychrag_api/main.py`
- Enforce business rules:
  - Only one active template per function tag
  - Auto-increment version numbers
  - Validate template content as valid LangChain PromptTemplate format
- Error handling for validation failures, not found errors, database constraints

**Out of scope:**
- Frontend UI (handled in T03)
- Integration with existing functions (handled in T04)
- Template versioning history/diff views
- Template rollback functionality
- Template export/import

## Implementation plan

### Backend

#### 1. Create Pydantic schemas

File: `/src/psychrag_api/schemas/templates.py`

```python
from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import List


class PromptTemplateBase(BaseModel):
    """Base schema for prompt template."""
    function_tag: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    template_content: str = Field(..., min_length=1)


class PromptTemplateCreate(BaseModel):
    """Schema for creating a new template version."""
    title: str = Field(..., min_length=1, max_length=255)
    template_content: str = Field(..., min_length=1)

    @validator('template_content')
    def validate_template_format(cls, v):
        """Validate that template can be parsed as LangChain PromptTemplate."""
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate
        try:
            LCPromptTemplate.from_template(v)
        except Exception as e:
            raise ValueError(f"Invalid PromptTemplate format: {e}")
        return v


class PromptTemplateUpdate(BaseModel):
    """Schema for updating an existing template."""
    title: str | None = Field(None, min_length=1, max_length=255)
    template_content: str | None = Field(None, min_length=1)

    @validator('template_content')
    def validate_template_format(cls, v):
        """Validate that template can be parsed as LangChain PromptTemplate."""
        if v is None:
            return v
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate
        try:
            LCPromptTemplate.from_template(v)
        except Exception as e:
            raise ValueError(f"Invalid PromptTemplate format: {e}")
        return v


class PromptTemplateResponse(PromptTemplateBase):
    """Schema for template response."""
    id: int
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateSummary(BaseModel):
    """Summary of a template version for list views."""
    version: int
    title: str
    is_active: bool
    created_at: datetime


class FunctionTemplateSummary(BaseModel):
    """Summary of all versions for a function tag."""
    function_tag: str
    active_version: int | None
    versions: List[TemplateSummary]


class TemplateListResponse(BaseModel):
    """Response for listing all template functions."""
    templates: List[FunctionTemplateSummary]
```

#### 2. Create router with endpoints

File: `/src/psychrag_api/routers/templates.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List

from psychrag.data.database import get_session
from psychrag.data.models.prompt_template import PromptTemplate
from psychrag_api.schemas.templates import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    FunctionTemplateSummary,
    TemplateSummary,
    TemplateListResponse,
)

router = APIRouter(prefix="/settings/templates", tags=["Settings"])


@router.get("/", response_model=TemplateListResponse)
def list_all_templates(session: Session = Depends(get_session)):
    """List all template functions with version summaries."""
    # Get all templates ordered by function_tag and version
    all_templates = session.query(PromptTemplate).order_by(
        PromptTemplate.function_tag,
        desc(PromptTemplate.version)
    ).all()

    # Group by function_tag
    grouped = {}
    for template in all_templates:
        if template.function_tag not in grouped:
            grouped[template.function_tag] = []
        grouped[template.function_tag].append(template)

    # Build response
    function_summaries = []
    for function_tag, templates in grouped.items():
        active_version = None
        version_summaries = []

        for template in templates:
            if template.is_active:
                active_version = template.version
            version_summaries.append(TemplateSummary(
                version=template.version,
                title=template.title,
                is_active=template.is_active,
                created_at=template.created_at
            ))

        function_summaries.append(FunctionTemplateSummary(
            function_tag=function_tag,
            active_version=active_version,
            versions=version_summaries
        ))

    return TemplateListResponse(templates=function_summaries)


@router.get("/{function_tag}", response_model=List[PromptTemplateResponse])
def get_templates_for_function(
    function_tag: str,
    session: Session = Depends(get_session)
):
    """Get all versions for a specific function tag."""
    templates = session.query(PromptTemplate).filter(
        PromptTemplate.function_tag == function_tag
    ).order_by(desc(PromptTemplate.version)).all()

    if not templates:
        raise HTTPException(
            status_code=404,
            detail=f"No templates found for function_tag: {function_tag}"
        )

    return templates


@router.get("/{function_tag}/{version}", response_model=PromptTemplateResponse)
def get_template_version(
    function_tag: str,
    version: int,
    session: Session = Depends(get_session)
):
    """Get a specific template version."""
    template = session.query(PromptTemplate).filter(
        PromptTemplate.function_tag == function_tag,
        PromptTemplate.version == version
    ).first()

    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {function_tag} v{version}"
        )

    return template


@router.post("/{function_tag}", response_model=PromptTemplateResponse, status_code=201)
def create_new_version(
    function_tag: str,
    template_data: PromptTemplateCreate,
    session: Session = Depends(get_session)
):
    """Create a new version for a function tag (auto-increment version)."""
    # Get the highest existing version for this function_tag
    max_version_result = session.query(
        PromptTemplate.version
    ).filter(
        PromptTemplate.function_tag == function_tag
    ).order_by(desc(PromptTemplate.version)).first()

    new_version = 1 if max_version_result is None else max_version_result[0] + 1

    # Create new template (not active by default)
    new_template = PromptTemplate(
        function_tag=function_tag,
        version=new_version,
        title=template_data.title,
        template_content=template_data.template_content,
        is_active=False
    )

    session.add(new_template)
    session.commit()
    session.refresh(new_template)

    return new_template


@router.put("/{function_tag}/{version}", response_model=PromptTemplateResponse)
def update_template(
    function_tag: str,
    version: int,
    template_data: PromptTemplateUpdate,
    session: Session = Depends(get_session)
):
    """Update an existing template's content (overwrite)."""
    template = session.query(PromptTemplate).filter(
        PromptTemplate.function_tag == function_tag,
        PromptTemplate.version == version
    ).first()

    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {function_tag} v{version}"
        )

    # Update fields if provided
    if template_data.title is not None:
        template.title = template_data.title
    if template_data.template_content is not None:
        template.template_content = template_data.template_content

    session.commit()
    session.refresh(template)

    return template


@router.put("/{function_tag}/{version}/activate", response_model=PromptTemplateResponse)
def set_active_version(
    function_tag: str,
    version: int,
    session: Session = Depends(get_session)
):
    """Set a specific version as the active template for a function tag."""
    # Verify the target template exists
    target_template = session.query(PromptTemplate).filter(
        PromptTemplate.function_tag == function_tag,
        PromptTemplate.version == version
    ).first()

    if not target_template:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found: {function_tag} v{version}"
        )

    # Deactivate all other versions for this function_tag
    session.query(PromptTemplate).filter(
        PromptTemplate.function_tag == function_tag,
        PromptTemplate.is_active == True
    ).update({"is_active": False})

    # Activate the target version
    target_template.is_active = True

    session.commit()
    session.refresh(target_template)

    return target_template
```

#### 3. Register router in main app

File: `/src/psychrag_api/main.py`

Add import:
```python
from psychrag_api.routers import (
    chunking,
    conversion,
    corpus,
    init,
    rag,
    sanitization,
    settings,
    templates,  # Add this
    vectorization,
)
```

Add router:
```python
# After existing router includes
app.include_router(templates.router)
```

Add OpenAPI tag (in the `openapi_tags` list):
```python
{
    "name": "Templates",
    "description": "Prompt template management. Create, edit, and manage versioned prompt templates.",
},
```

**Note**: Since templates are under `/settings/templates/`, they will appear under the "Settings" tag in Swagger UI.

#### 4. Error handling and validation

**HTTP status codes:**
- `200 OK`: Successful GET/PUT
- `201 Created`: Successful POST
- `404 Not Found`: Template or function_tag not found
- `400 Bad Request`: Validation errors (invalid PromptTemplate format, invalid data)
- `500 Internal Server Error`: Database errors

**Validation:**
- Pydantic validators ensure template_content is valid LangChain PromptTemplate format
- Version must be positive integer
- Function_tag and title must not be empty

**Database constraints:**
- UNIQUE(function_tag, version) prevents duplicate versions (raises 500, could be caught and returned as 409 Conflict)
- NOT NULL constraints ensure required fields

#### 5. Transaction management

Use SQLAlchemy session transactions:
- All write operations (POST, PUT) commit within the endpoint
- Use `session.refresh()` to get updated data after commit
- Rollback on errors (handled by FastAPI dependency injection cleanup)

### Other / cross-cutting

**API Documentation:**
- Each endpoint has docstring describing its purpose
- Pydantic models auto-generate OpenAPI schemas
- Example payloads in Swagger UI

**Logging:**
- Consider adding logging for template activations and creations (not critical for this ticket)

**Performance:**
- Queries are indexed on `function_tag` and `(function_tag, is_active)`
- List endpoint groups templates in Python (could be optimized with SQL GROUP BY if needed)

## Unit tests

**Target**: `tests/unit/test_templates_api.py`

Use FastAPI's `TestClient` for API testing:

```python
import pytest
from fastapi.testclient import TestClient
from psychrag_api.main import app
from psychrag.data.database import get_session
from psychrag.data.models.prompt_template import PromptTemplate


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_templates(session):
    """Create sample templates for testing."""
    templates = [
        PromptTemplate(
            function_tag="test_function",
            version=1,
            title="Test Template V1",
            template_content="Test template with {variable}",
            is_active=True
        ),
        PromptTemplate(
            function_tag="test_function",
            version=2,
            title="Test Template V2",
            template_content="Updated template with {variable}",
            is_active=False
        ),
    ]
    session.add_all(templates)
    session.commit()
    return templates
```

**Test cases:**

1. **GET /settings/templates/**
   - `test_list_all_templates_empty()`: Returns empty list when no templates
   - `test_list_all_templates()`: Returns grouped templates by function_tag
   - `test_list_shows_active_version()`: Active version is correctly identified

2. **GET /settings/templates/{function_tag}**
   - `test_get_templates_for_function()`: Returns all versions for a function
   - `test_get_templates_for_function_not_found()`: Returns 404 for unknown function_tag
   - `test_get_templates_ordered_by_version()`: Versions are in descending order

3. **GET /settings/templates/{function_tag}/{version}**
   - `test_get_specific_version()`: Returns correct template
   - `test_get_version_not_found()`: Returns 404 for non-existent version

4. **POST /settings/templates/{function_tag}**
   - `test_create_first_version()`: Creates v1 when no templates exist
   - `test_create_auto_increment_version()`: Creates v3 when v1 and v2 exist
   - `test_create_new_version_not_active()`: New version has is_active=False
   - `test_create_invalid_template_format()`: Returns 400 for invalid PromptTemplate syntax

5. **PUT /settings/templates/{function_tag}/{version}**
   - `test_update_template_content()`: Updates template_content successfully
   - `test_update_template_title()`: Updates title successfully
   - `test_update_template_not_found()`: Returns 404 for non-existent template
   - `test_update_invalid_template_format()`: Returns 400 for invalid PromptTemplate syntax

6. **PUT /settings/templates/{function_tag}/{version}/activate**
   - `test_activate_version()`: Sets is_active=True for target version
   - `test_activate_deactivates_others()`: Deactivates all other versions for same function_tag
   - `test_activate_only_affects_same_function()`: Doesn't affect other function_tags
   - `test_activate_not_found()`: Returns 404 for non-existent version

**Example test:**
```python
def test_create_auto_increment_version(client, sample_templates):
    response = client.post(
        "/settings/templates/test_function",
        json={
            "title": "Test Template V3",
            "template_content": "New template with {variable}"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["version"] == 3
    assert data["is_active"] == False
    assert data["title"] == "Test Template V3"
```

## Manual test plan

After implementing this ticket, test via Swagger UI (`http://localhost:8000/docs`):

### 1. Test listing templates

**Request:**
```
GET /settings/templates/
```

**Expected response:**
```json
{
  "templates": [
    {
      "function_tag": "query_expansion",
      "active_version": 1,
      "versions": [
        {
          "version": 1,
          "title": "Query Expansion - Multi-Query Expansion (MQE) and HyDE",
          "is_active": true,
          "created_at": "2025-11-28T10:00:00Z"
        }
      ]
    },
    // ... other 3 function tags
  ]
}
```

### 2. Test getting all versions for a function

**Request:**
```
GET /settings/templates/query_expansion
```

**Expected response:** List of all versions for `query_expansion`, ordered by version DESC

### 3. Test getting specific version

**Request:**
```
GET /settings/templates/query_expansion/1
```

**Expected response:** Full template object with `template_content` field

### 4. Test creating new version

**Request:**
```
POST /settings/templates/query_expansion
Content-Type: application/json

{
  "title": "Query Expansion V2 - Improved",
  "template_content": "You are a query expansion assistant...\n\nUser query: {query}\n\nGenerate {n} alternatives."
}
```

**Expected response:** Status 201, template object with `version=2`, `is_active=false`

### 5. Test updating template

**Request:**
```
PUT /settings/templates/query_expansion/2
Content-Type: application/json

{
  "template_content": "Updated content with {query} and {n}"
}
```

**Expected response:** Status 200, updated template object

### 6. Test activating version

**Request:**
```
PUT /settings/templates/query_expansion/2/activate
```

**Expected response:** Status 200, template with `is_active=true`

**Verify side effect:**
```
GET /settings/templates/query_expansion/1
```
Should show `is_active=false`

### 7. Test error cases

**Invalid template format:**
```
POST /settings/templates/test_function
Content-Type: application/json

{
  "title": "Invalid Template",
  "template_content": "Template with unclosed brace {"
}
```

**Expected:** Status 400, error message about invalid PromptTemplate format

**Non-existent template:**
```
GET /settings/templates/query_expansion/999
```

**Expected:** Status 404, error message "Template not found: query_expansion v999"

## Dependencies and sequencing

**Depends on:**
- T01 (Database schema and migration) - MUST be completed first

**Blocks:**
- T03 (Settings UI) - frontend needs these endpoints

**Can run in parallel with:**
- T04 (Integration) - as long as T01 is done

## Clarifications and assumptions

### Assumptions made:

1. **One active template per function**: Enforced by deactivating all other versions when activating a new one - **CONFIRM**: This is the correct behavior (no need for user confirmation before deactivating?)

2. **New versions default to inactive**: When creating a new version via POST, it's created with `is_active=False` - user must explicitly activate it via `/activate` endpoint - **CONFIRM**: Is this the desired workflow?

3. **Overwrite semantics**: PUT endpoint allows overwriting template content in-place (does not create new version) - **CONFIRM**: This matches PRD requirement "Save directly to that version (overwrite)"

4. **No version deletion**: No DELETE endpoint for templates - once created, versions persist - **CONFIRM**: Is this acceptable, or should we support soft/hard delete?

5. **Template validation**: Using LangChain's `PromptTemplate.from_template()` to validate format - this will catch syntax errors but not semantic issues (e.g., missing variables) - **CONFIRM**: Is this sufficient validation?

6. **Function tags are freeform**: No validation that function_tag matches known functions - allows extensibility for future template types - **CONFIRM**: Is this acceptable, or should we validate against a whitelist?

7. **Concurrent activation**: No locking mechanism for activating versions - if two users activate different versions simultaneously, last write wins - **CLARIFY**: Is this a concern? Should we add optimistic locking (e.g., check `updated_at` timestamp)?

8. **Error responses**: Using standard HTTP status codes without custom error schemas - **CONFIRM**: Is this sufficient, or should we create custom error response schemas?

### Blocking questions:

**NONE** - Can proceed with implementation. Address assumptions in code review.

---

**Before implementing, review the Clarifications and assumptions section with the product owner. If any blocking item is unresolved, get explicit answers or update the ticket accordingly before writing code.**
