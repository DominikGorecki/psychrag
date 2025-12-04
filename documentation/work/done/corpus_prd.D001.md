# T001 - Backend API for corpus management - COMPLETE

## Context

- Link back to the PRD: [corpus_prd.md](corpus_prd.md)
- Specific sections: Section 3 (data filtering), Section 4 (overview statistics)
- This ticket implements the backend API endpoints needed to support the corpus management feature. The corpus represents works that have completed both content and heading chunking, making them ready for vectorization and RAG operations.

## Outcome

Backend API provides endpoints that return:
1. A filtered list of works where both `content_chunks` and `heading_chunks` are marked as "completed"
2. Statistics on chunk vectorization status broken down by all four vector status values
3. Individual work details including sanitized markdown file paths

## Scope

### In scope:
- New `/corpus` router in `src/psychrag_api/routers/corpus.py`
- GET endpoint for listing corpus works with filtering
- GET endpoint for corpus statistics (work count + chunk counts by vector status)
- GET endpoint for individual work details -- one call for entire list
- GET endpoint for retrieving sanitized markdown content
- Pydantic schemas for all request/response models
- Database queries using SQLAlchemy ORM

### Out of scope:
- Frontend implementation (handled in T003, T004)
- Any modification or creation of works (this is read-only)
- Navigation changes (handled in T002)
- Vectorization operations (separate feature)

## Implementation plan

### Backend

#### 1. Create API router file

Create `src/psychrag_api/routers/corpus.py` with the following structure:

```python
"""
Corpus Router - Read-only access to works ready for vectorization.

Endpoints:
    GET  /corpus/stats                 - Get corpus statistics
    GET  /corpus/works                 - List all corpus works
    GET  /corpus/work/{work_id}        - Get specific work details
    GET  /corpus/work/{work_id}/content - Get sanitized markdown content
"""
```

#### 2. Create Pydantic schemas

Create `src/psychrag_api/schemas/corpus.py`:

```python
from pydantic import BaseModel
from typing import Optional

class ChunkVectorStats(BaseModel):
    no_vec: int
    to_vec: int
    vec: int
    vec_err: int

class CorpusStatsResponse(BaseModel):
    total_works: int
    chunk_stats: ChunkVectorStats

class CorpusWorkListItem(BaseModel):
    id: int
    title: str
    authors: Optional[str]
    sanitized_path: str

class CorpusWorksResponse(BaseModel):
    works: list[CorpusWorkListItem]
    total: int

class CorpusWorkDetailResponse(BaseModel):
    id: int
    title: str
    authors: Optional[str]
    year: Optional[int]
    publisher: Optional[str]
    sanitized_path: str
    sanitized_hash: str

class SanitizedContentResponse(BaseModel):
    content: str
    filename: str
    work_id: int
    work_title: str
```

#### 3. Implement database queries

In `src/psychrag_api/routers/corpus.py`, implement query functions:

**Query for corpus works:**
```python
def get_corpus_works(session):
    """
    Get all works where processing_status has both content_chunks
    and heading_chunks set to 'completed'.
    """
    works = session.query(Work).all()
    corpus_works = []

    for work in works:
        if not work.processing_status:
            continue

        status = work.processing_status
        if (status.get("content_chunks") == "completed" and
            status.get("heading_chunks") == "completed" and
            work.files and "sanitized" in work.files):
            corpus_works.append(work)

    return corpus_works
```

**Query for chunk statistics:**
```python
from sqlalchemy import func
from psychrag.data.models.chunk import Chunk

def get_chunk_vector_stats(session):
    """
    Count chunks by vector_status for all corpus works.
    """
    # Get all corpus work IDs
    corpus_work_ids = [w.id for w in get_corpus_works(session)]

    if not corpus_work_ids:
        return {"no_vec": 0, "to_vec": 0, "vec": 0, "vec_err": 0}

    # Count by vector_status
    stats = session.query(
        Chunk.vector_status,
        func.count(Chunk.id)
    ).filter(
        Chunk.work_id.in_(corpus_work_ids)
    ).group_by(
        Chunk.vector_status
    ).all()

    # Build result with all statuses
    result = {"no_vec": 0, "to_vec": 0, "vec": 0, "vec_err": 0}
    for status, count in stats:
        if status in result:
            result[status] = count

    return result
```

#### 4. Implement API endpoints

**GET /corpus/stats:**
```python
@router.get(
    "/stats",
    response_model=CorpusStatsResponse,
    summary="Get corpus statistics",
    description="Get count of corpus works and chunk vectorization statistics.",
)
async def get_corpus_stats() -> CorpusStatsResponse:
    with get_session() as session:
        works = get_corpus_works(session)
        chunk_stats = get_chunk_vector_stats(session)

        return CorpusStatsResponse(
            total_works=len(works),
            chunk_stats=ChunkVectorStats(**chunk_stats)
        )
```

**GET /corpus/works:**
```python
@router.get(
    "/works",
    response_model=CorpusWorksResponse,
    summary="List corpus works",
    description="Get all works that have completed chunking and are ready for vectorization.",
)
async def list_corpus_works() -> CorpusWorksResponse:
    with get_session() as session:
        works = get_corpus_works(session)

        work_items = [
            CorpusWorkListItem(
                id=work.id,
                title=work.title,
                authors=work.authors,
                sanitized_path=work.files["sanitized"]["path"]
            )
            for work in works
        ]

        # Sort by ID descending (newest first)
        work_items.sort(key=lambda x: x.id, reverse=True)

        return CorpusWorksResponse(
            works=work_items,
            total=len(work_items)
        )
```

**GET /corpus/work/{work_id}:**
```python
@router.get(
    "/work/{work_id}",
    response_model=CorpusWorkDetailResponse,
    summary="Get corpus work details",
    description="Get detailed information about a specific corpus work.",
)
async def get_corpus_work_detail(work_id: int) -> CorpusWorkDetailResponse:
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )

        # Verify this is a corpus work
        if not work.processing_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Work {work_id} has no processing status"
            )

        status_obj = work.processing_status
        if (status_obj.get("content_chunks") != "completed" or
            status_obj.get("heading_chunks") != "completed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Work {work_id} has not completed chunking"
            )

        if not work.files or "sanitized" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have a sanitized file"
            )

        sanitized_info = work.files["sanitized"]

        return CorpusWorkDetailResponse(
            id=work.id,
            title=work.title,
            authors=work.authors,
            year=work.year,
            publisher=work.publisher,
            sanitized_path=sanitized_info["path"],
            sanitized_hash=sanitized_info["hash"]
        )
```

**GET /corpus/work/{work_id}/content:**
```python
from pathlib import Path

@router.get(
    "/work/{work_id}/content",
    response_model=SanitizedContentResponse,
    summary="Get sanitized markdown content",
    description="Retrieve the sanitized markdown file content for a corpus work.",
)
async def get_sanitized_content(work_id: int) -> SanitizedContentResponse:
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )

        if not work.files or "sanitized" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have a sanitized file"
            )

        sanitized_path = Path(work.files["sanitized"]["path"])

        if not sanitized_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sanitized file not found on disk: {sanitized_path}"
            )

        try:
            content = sanitized_path.read_text(encoding="utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read sanitized file: {str(e)}"
            )

        return SanitizedContentResponse(
            content=content,
            filename=sanitized_path.name,
            work_id=work.id,
            work_title=work.title
        )
```

#### 5. Register router in main API

Update `src/psychrag_api/main.py` to include the corpus router:

```python
from psychrag_api.routers import corpus

app.include_router(corpus.router, prefix="/corpus", tags=["corpus"])
```

#### 6. Error handling and validation

- All endpoints return 404 if work not found
- Validate that works are actually corpus works (completed chunking)
- Validate that sanitized files exist before trying to read them
- Handle file I/O errors gracefully with 500 responses
- Use proper HTTP status codes throughout

#### 7. Database session management

- Use `get_session()` context manager consistently
- Ensure sessions are closed after each request
- Don't hold sessions open longer than necessary

## Unit tests

Create `tests/unit/test_corpus_router.py`:

### Test framework and setup
- Use pytest with FastAPI TestClient
- Mock database session using pytest fixtures
- Create fixture factories for Work and Chunk models

### Specific test cases

**Test `GET /corpus/stats`:**
- Returns correct total_works count for corpus works
- Returns correct chunk_stats with all four vector status counts
- Returns zero counts when no corpus works exist
- Excludes works without completed processing_status
- Excludes chunks from non-corpus works

**Test `GET /corpus/works`:**
- Returns all works with completed chunking
- Excludes works with incomplete content_chunks
- Excludes works with incomplete heading_chunks
- Excludes works without sanitized files
- Returns works sorted by ID descending
- Returns empty list when no corpus works exist

**Test `GET /corpus/work/{work_id}`:**
- Returns correct work details for valid corpus work
- Returns 404 for non-existent work ID
- Returns 400 for work without processing_status
- Returns 400 for work with incomplete chunking
- Returns 404 for work without sanitized file
- Includes all required fields in response

**Test `GET /corpus/work/{work_id}/content`:**
- Returns correct content from sanitized file
- Returns correct filename
- Returns 404 for non-existent work ID
- Returns 404 for work without sanitized file
- Returns 404 when file path doesn't exist on disk
- Returns 500 when file read fails

### Edge cases to test
- Works with null processing_status
- Works with partial processing_status (only one chunk type completed)
- Works with processing_status but no files metadata
- Works with files metadata but no sanitized entry
- Empty database scenario
- Multiple works with different processing states