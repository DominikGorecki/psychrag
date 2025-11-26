"""
Chunking Router - Chunking operations for works with sanitized files.

Endpoints:
    GET  /chunking/works                                      - List works with sanitized files
    GET  /chunking/work/{work_id}                            - Get work detail
    GET  /chunking/work/{work_id}/sanitized/content          - Get sanitized content
    PUT  /chunking/work/{work_id}/sanitized/content          - Update sanitized content
    POST /chunking/work/{work_id}/extract-sanitized-titles   - Extract sanitized titles
    GET  /chunking/work/{work_id}/san-titles/content         - Get sanitized titles content
    PUT  /chunking/work/{work_id}/san-titles/content         - Update sanitized titles content
    GET  /chunking/work/{work_id}/vec-suggestions/content    - Get vec suggestions content
    PUT  /chunking/work/{work_id}/vec-suggestions/content    - Update vec suggestions content
    POST /chunking/work/{work_id}/apply-heading-chunks       - Apply heading chunking
    POST /chunking/work/{work_id}/apply-content-chunks       - Apply content chunking
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, status

from psychrag.data.database import get_session
from psychrag.data.models.work import Work
from psychrag.sanitization import extract_titles_from_work, HashMismatchError
from psychrag.chunking.chunk_headings import chunk_headings
from psychrag.chunking.content_chunking import chunk_content
from psychrag.utils.file_utils import compute_file_hash, set_file_writable, set_file_readonly
from psychrag_api.schemas.chunking import (
    WorkListResponse,
    WorkListItem,
    WorkDetailResponse,
    FileStatusInfo,
    SanitizedContentResponse,
    UpdateSanitizedContentRequest,
    ExtractSanitizedTitlesRequest,
    ExtractSanitizedTitlesResponse,
    SanTitlesContentResponse,
    UpdateSanTitlesContentRequest,
    VecSuggestionsContentResponse,
    UpdateVecSuggestionsContentRequest,
    ApplyHeadingChunksResponse,
    ApplyContentChunksResponse,
)

router = APIRouter(tags=["chunking"])


def _get_file_status(work: Work, file_key: str) -> FileStatusInfo:
    """Helper to get file status information."""
    if not work.files or file_key not in work.files:
        return FileStatusInfo(exists=False, path=None, hash=None, hash_match=None)
    
    file_info = work.files[file_key]
    file_path = Path(file_info["path"])
    stored_hash = file_info["hash"]
    
    if not file_path.exists():
        return FileStatusInfo(
            exists=False,
            path=str(file_path),
            hash=stored_hash,
            hash_match=False
        )
    
    current_hash = compute_file_hash(file_path)
    hash_match = current_hash == stored_hash
    
    return FileStatusInfo(
        exists=True,
        path=str(file_path),
        hash=stored_hash,
        hash_match=hash_match
    )


@router.get(
    "/works",
    response_model=WorkListResponse,
    summary="List works with sanitized files",
    description="Returns all works that have sanitized files ready for chunking.",
)
async def list_works_for_chunking() -> WorkListResponse:
    """List all works that have sanitized files."""
    with get_session() as session:
        works = session.query(Work).all()
    
        work_items = []
        for work in works:
            # Only include works that have sanitized file
            if not work.files or "sanitized" not in work.files:
                continue
            
            # Get processing status
            heading_status = None
            content_status = None
            if work.processing_status:
                heading_status = work.processing_status.get("heading_chunks")
                content_status = work.processing_status.get("content_chunks")
            
            work_items.append(
                WorkListItem(
                    id=work.id,
                    title=work.title,
                    authors=work.authors,
                    year=work.year,
                    work_type=work.work_type,
                    has_sanitized=True,
                    heading_chunks_status=heading_status,
                    content_chunks_status=content_status,
                )
            )
        
        return WorkListResponse(works=work_items, total=len(work_items))


@router.get(
    "/work/{work_id}",
    response_model=WorkDetailResponse,
    summary="Get work detail",
    description="Returns detailed information about a work including file statuses.",
)
async def get_work_detail(work_id: int) -> WorkDetailResponse:
    """Get detailed work information."""
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        # Get file statuses
        file_statuses = {
            "sanitized": _get_file_status(work, "sanitized"),
            "sanitized_titles": _get_file_status(work, "sanitized_titles"),
            "vec_suggestions": _get_file_status(work, "vec_suggestions"),
        }
        
        return WorkDetailResponse(
            id=work.id,
            title=work.title,
            authors=work.authors,
            year=work.year,
            work_type=work.work_type,
            files=file_statuses,
            processing_status=work.processing_status,
        )


@router.get(
    "/work/{work_id}/sanitized/content",
    response_model=SanitizedContentResponse,
    summary="Get sanitized file content",
    description="Returns the content of the sanitized file.",
)
async def get_sanitized_content(work_id: int) -> SanitizedContentResponse:
    """Get sanitized file content."""
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
                detail=f"Work {work_id} does not have sanitized file"
            )
        
        file_info = work.files["sanitized"]
        file_path = Path(file_info["path"])
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sanitized file not found on disk: {file_path}"
            )
        
        content = file_path.read_text(encoding='utf-8')
        current_hash = compute_file_hash(file_path)
        
        return SanitizedContentResponse(
            content=content,
            filename=file_path.name,
            current_hash=current_hash
        )


@router.put(
    "/work/{work_id}/sanitized/content",
    response_model=SanitizedContentResponse,
    summary="Update sanitized file content",
    description="Updates the content of the sanitized file and recalculates hash.",
)
async def update_sanitized_content(
    work_id: int,
    request: UpdateSanitizedContentRequest
) -> SanitizedContentResponse:
    """Update sanitized file content."""
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
                detail=f"Work {work_id} does not have sanitized file"
            )
        
        file_info = work.files["sanitized"]
        file_path = Path(file_info["path"])
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sanitized file not found on disk: {file_path}"
            )
        
        try:
            # Make file writable if it's read-only
            set_file_writable(file_path)
            
            # Write new content
            file_path.write_text(request.content, encoding='utf-8')
            
            # Set back to read-only
            set_file_readonly(file_path)
            
            # Compute new hash
            new_hash = compute_file_hash(file_path)
            
            # Update work.files with new hash (recreate dict to trigger SQLAlchemy change detection)
            updated_files = dict(work.files)
            updated_files["sanitized"] = {
                "path": str(file_path.resolve()),
                "hash": new_hash
            }
            work.files = updated_files
            
            session.commit()
            session.refresh(work)
            
            return SanitizedContentResponse(
                content=request.content,
                filename=file_path.name,
                current_hash=new_hash
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update sanitized file: {e}"
            )


@router.post(
    "/work/{work_id}/extract-sanitized-titles",
    response_model=ExtractSanitizedTitlesResponse,
    summary="Extract sanitized titles",
    description="Extracts titles from sanitized markdown file.",
)
async def extract_sanitized_titles(
    work_id: int,
    request: ExtractSanitizedTitlesRequest
) -> ExtractSanitizedTitlesResponse:
    """Extract titles from sanitized file."""
    try:
        output_path = extract_titles_from_work(
            work_id=work_id,
            source_key="sanitized",
            force=request.force,
            verbose=True
        )
        
        return ExtractSanitizedTitlesResponse(
            success=True,
            message="Successfully extracted sanitized titles",
            output_path=str(output_path)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {e}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract titles: {e}"
        )


@router.get(
    "/work/{work_id}/san-titles/content",
    response_model=SanTitlesContentResponse,
    summary="Get sanitized titles content",
    description="Returns the content of the sanitized_titles file.",
)
async def get_san_titles_content(work_id: int) -> SanTitlesContentResponse:
    """Get sanitized titles file content."""
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "sanitized_titles" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have sanitized_titles file"
            )
        
        file_info = work.files["sanitized_titles"]
        file_path = Path(file_info["path"])
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sanitized titles file not found on disk: {file_path}"
            )
        
        content = file_path.read_text(encoding='utf-8')
        current_hash = compute_file_hash(file_path)
        
        return SanTitlesContentResponse(
            content=content,
            filename=file_path.name,
            current_hash=current_hash
        )


@router.put(
    "/work/{work_id}/san-titles/content",
    response_model=SanTitlesContentResponse,
    summary="Update sanitized titles content",
    description="Updates the content of the sanitized_titles file and recalculates hash.",
)
async def update_san_titles_content(
    work_id: int,
    request: UpdateSanTitlesContentRequest
) -> SanTitlesContentResponse:
    """Update sanitized titles file content."""
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "sanitized_titles" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have sanitized_titles file"
            )
        
        file_info = work.files["sanitized_titles"]
        file_path = Path(file_info["path"])
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sanitized titles file not found on disk: {file_path}"
            )
        
        try:
            # Make file writable if it's read-only
            set_file_writable(file_path)
            
            # Write new content
            file_path.write_text(request.content, encoding='utf-8')
            
            # Set back to read-only
            set_file_readonly(file_path)
            
            # Compute new hash
            new_hash = compute_file_hash(file_path)
            
            # Update work.files with new hash (recreate dict to trigger SQLAlchemy change detection)
            updated_files = dict(work.files)
            updated_files["sanitized_titles"] = {
                "path": str(file_path.resolve()),
                "hash": new_hash
            }
            work.files = updated_files
            
            session.commit()
            session.refresh(work)
            
            return SanTitlesContentResponse(
                content=request.content,
                filename=file_path.name,
                current_hash=new_hash
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update sanitized titles file: {e}"
            )


@router.get(
    "/work/{work_id}/vec-suggestions/content",
    response_model=VecSuggestionsContentResponse,
    summary="Get vec suggestions content",
    description="Returns the content of the vec_suggestions file.",
)
async def get_vec_suggestions_content(work_id: int) -> VecSuggestionsContentResponse:
    """Get vec suggestions file content."""
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "vec_suggestions" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have vec_suggestions file"
            )
        
        file_info = work.files["vec_suggestions"]
        file_path = Path(file_info["path"])
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vec suggestions file not found on disk: {file_path}"
            )
        
        content = file_path.read_text(encoding='utf-8')
        current_hash = compute_file_hash(file_path)
        
        return VecSuggestionsContentResponse(
            content=content,
            filename=file_path.name,
            current_hash=current_hash
        )


@router.put(
    "/work/{work_id}/vec-suggestions/content",
    response_model=VecSuggestionsContentResponse,
    summary="Update vec suggestions content",
    description="Updates the content of the vec_suggestions file and recalculates hash.",
)
async def update_vec_suggestions_content(
    work_id: int,
    request: UpdateVecSuggestionsContentRequest
) -> VecSuggestionsContentResponse:
    """Update vec suggestions file content."""
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "vec_suggestions" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have vec_suggestions file"
            )
        
        file_info = work.files["vec_suggestions"]
        file_path = Path(file_info["path"])
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vec suggestions file not found on disk: {file_path}"
            )
        
        try:
            # Make file writable if it's read-only
            set_file_writable(file_path)
            
            # Write new content
            file_path.write_text(request.content, encoding='utf-8')
            
            # Set back to read-only
            set_file_readonly(file_path)
            
            # Compute new hash
            new_hash = compute_file_hash(file_path)
            
            # Update work.files with new hash (recreate dict to trigger SQLAlchemy change detection)
            updated_files = dict(work.files)
            updated_files["vec_suggestions"] = {
                "path": str(file_path.resolve()),
                "hash": new_hash
            }
            work.files = updated_files
            
            session.commit()
            session.refresh(work)
            
            return VecSuggestionsContentResponse(
                content=request.content,
                filename=file_path.name,
                current_hash=new_hash
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update vec suggestions file: {e}"
            )


@router.post(
    "/work/{work_id}/apply-heading-chunks",
    response_model=ApplyHeadingChunksResponse,
    summary="Apply heading chunks",
    description="Runs chunk_headings to create heading-based chunks.",
)
async def apply_heading_chunks(work_id: int) -> ApplyHeadingChunksResponse:
    """Apply heading chunking."""
    try:
        chunks_created = chunk_headings(work_id=work_id, verbose=True)
        
        return ApplyHeadingChunksResponse(
            success=True,
            message=f"Successfully created {chunks_created} heading chunks",
            chunks_created=chunks_created
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {e}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply heading chunks: {e}"
        )


@router.post(
    "/work/{work_id}/apply-content-chunks",
    response_model=ApplyContentChunksResponse,
    summary="Apply content chunks",
    description="Runs content_chunking to create paragraph-based chunks.",
)
async def apply_content_chunks(work_id: int) -> ApplyContentChunksResponse:
    """Apply content chunking."""
    try:
        chunks_created = chunk_content(work_id=work_id, verbose=True)
        
        return ApplyContentChunksResponse(
            success=True,
            message=f"Successfully created {chunks_created} content chunks",
            chunks_created=chunks_created
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {e}"
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply content chunks: {e}"
        )
