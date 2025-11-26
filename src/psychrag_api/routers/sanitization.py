"""
Sanitization Router - Content sanitization operations.

Endpoints:
    GET  /sanitization/works                              - List all works
    GET  /sanitization/work/{work_id}                     - Get work detail
    POST /sanitization/work/{work_id}/extract-titles      - Extract titles
    POST /sanitization/work/{work_id}/suggest-title-changes - Suggest changes
    POST /sanitization/work/{work_id}/apply-title-changes - Apply changes
    POST /sanitization/work/{work_id}/skip-apply          - Skip and copy
    POST /sanitization/extract-toc                        - Extract TOC (legacy)
    POST /sanitization/extract-titles                     - Extract titles (legacy)
    POST /sanitization/suggest-changes                    - Suggest changes (legacy)
    POST /sanitization/apply-changes                      - Apply changes (legacy)
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, status

from psychrag.data.database import get_session
from psychrag.data.models.work import Work
from psychrag.sanitization import (
    extract_titles_from_work,
    suggest_heading_changes_from_work,
    apply_title_changes_from_work,
    skip_apply_from_work,
    build_prompt_for_work,
    save_title_changes_from_response,
    HashMismatchError,
)
from psychrag.utils.file_utils import compute_file_hash, set_file_writable, set_file_readonly
from psychrag_api.schemas.sanitization import (
    # Legacy schemas
    ApplyChangesRequest,
    ApplyChangesResponse,
    ExtractTitlesRequest,
    ExtractTitlesResponse,
    ExtractTOCRequest,
    ExtractTOCResponse,
    SuggestChangesRequest,
    SuggestChangesResponse,
    # New work-based schemas
    WorkListResponse,
    WorkListItem,
    WorkDetailResponse,
    FileStatusInfo,
    ExtractTitlesFromWorkRequest,
    ExtractTitlesFromWorkResponse,
    SuggestTitleChangesRequest,
    SuggestTitleChangesResponse,
    ApplyTitleChangesRequest,
    ApplyTitleChangesResponse,
    SkipApplyRequest,
    SkipApplyResponse,
    TitlesContentResponse,
    UpdateTitlesContentRequest,
    PromptForWorkResponse,
    ManualTitleChangesRequest,
    ManualTitleChangesResponse,
)

router = APIRouter()


def _check_file_status(work: Work, file_key: str) -> FileStatusInfo:
    """Check the status of a file in the work's files metadata.
    
    Args:
        work: Work object.
        file_key: Key in the files JSON.
    
    Returns:
        FileStatusInfo with existence, path, hash, and validation status.
    """
    if not work.files or file_key not in work.files:
        return FileStatusInfo(
            exists=False,
            path=None,
            hash=None,
            hash_match=None,
            error=None
        )
    
    file_info = work.files[file_key]
    file_path = Path(file_info["path"])
    stored_hash = file_info["hash"]
    
    # Check if file exists on disk
    if not file_path.exists():
        return FileStatusInfo(
            exists=True,
            path=str(file_path),
            hash=stored_hash,
            hash_match=False,
            error=f"File not found on disk: {file_path}"
        )
    
    # Compute current hash and compare
    try:
        current_hash = compute_file_hash(file_path)
        hash_match = current_hash == stored_hash
        
        return FileStatusInfo(
            exists=True,
            path=str(file_path),
            hash=stored_hash,
            hash_match=hash_match,
            error=None if hash_match else f"Hash mismatch: stored={stored_hash[:16]}..., current={current_hash[:16]}..."
        )
    except Exception as e:
        return FileStatusInfo(
            exists=True,
            path=str(file_path),
            hash=stored_hash,
            hash_match=False,
            error=f"Error computing hash: {str(e)}"
        )


@router.get(
    "/works",
    response_model=WorkListResponse,
    summary="List all works",
    description="Get a list of all works in the database with their sanitization status.",
)
async def list_works() -> WorkListResponse:
    """
    List all works with their sanitization status.
    
    Returns works sorted by ID descending (newest first).
    """
    with get_session() as session:
        works = session.query(Work).order_by(Work.id.desc()).all()
        
        work_items = []
        needs_sanitization = 0
        
        for work in works:
            has_sanitized = bool(work.files and "sanitized" in work.files)
            has_original_markdown = bool(work.files and "original_markdown" in work.files)
            
            if not has_sanitized and has_original_markdown:
                needs_sanitization += 1
            
            work_items.append(WorkListItem(
                id=work.id,
                title=work.title,
                authors=work.authors,
                year=work.year,
                work_type=work.work_type,
                has_sanitized=has_sanitized,
                has_original_markdown=has_original_markdown,
            ))
        
        return WorkListResponse(
            works=work_items,
            total=len(work_items),
            needs_sanitization=needs_sanitization,
        )


@router.get(
    "/work/{work_id}",
    response_model=WorkDetailResponse,
    summary="Get work detail",
    description="Get detailed information about a work including all file statuses.",
)
async def get_work_detail(work_id: int) -> WorkDetailResponse:
    """
    Get detailed work information with file status validation.
    
    Checks existence and hash validation for all sanitization-related files.
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        # Check status of all relevant files
        original_markdown_status = _check_file_status(work, "original_markdown")
        titles_status = _check_file_status(work, "titles")
        title_changes_status = _check_file_status(work, "title_changes")
        sanitized_status = _check_file_status(work, "sanitized")
        
        return WorkDetailResponse(
            id=work.id,
            title=work.title,
            authors=work.authors,
            year=work.year,
            work_type=work.work_type,
            original_markdown=original_markdown_status,
            titles=titles_status,
            title_changes=title_changes_status,
            sanitized=sanitized_status,
        )


@router.post(
    "/work/{work_id}/extract-titles",
    response_model=ExtractTitlesFromWorkResponse,
    summary="Extract titles from work",
    description="Extract all headings from a work's markdown file.",
)
async def extract_titles_from_work_endpoint(
    work_id: int,
    request: ExtractTitlesFromWorkRequest
) -> ExtractTitlesFromWorkResponse:
    """
    Extract titles/headings from a work's markdown file.
    
    Creates a .titles.md file and updates the work's files metadata.
    """
    try:
        output_path = extract_titles_from_work(
            work_id=work_id,
            source_key=request.source_key,
            force=request.force,
            verbose=False
        )
        
        return ExtractTitlesFromWorkResponse(
            success=True,
            output_path=str(output_path),
            message=f"Titles extracted successfully to {output_path.name}"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {str(e)}. Use force=true to proceed anyway."
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract titles: {str(e)}"
        )


@router.post(
    "/work/{work_id}/suggest-title-changes",
    response_model=SuggestTitleChangesResponse,
    summary="Suggest title changes",
    description="Use AI to suggest heading hierarchy improvements for a work.",
)
async def suggest_title_changes_endpoint(
    work_id: int,
    request: SuggestTitleChangesRequest
) -> SuggestTitleChangesResponse:
    """
    Generate AI-suggested title changes for a work.
    
    Analyzes the document structure using LLM and creates a .title_changes.md file.
    """
    try:
        output_path = suggest_heading_changes_from_work(
            work_id=work_id,
            source_key=request.source_key,
            use_full_model=request.use_full_model,
            force=request.force,
            verbose=False
        )
        
        return SuggestTitleChangesResponse(
            success=True,
            output_path=str(output_path),
            message=f"Title changes suggested successfully to {output_path.name}"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {str(e)}. Use force=true to proceed anyway."
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest title changes: {str(e)}"
        )


@router.post(
    "/work/{work_id}/apply-title-changes",
    response_model=ApplyTitleChangesResponse,
    summary="Apply title changes",
    description="Apply the suggested title changes to create a sanitized markdown file.",
)
async def apply_title_changes_endpoint(
    work_id: int,
    request: ApplyTitleChangesRequest
) -> ApplyTitleChangesResponse:
    """
    Apply title changes to create sanitized markdown.
    
    Reads the .title_changes.md file and applies modifications to create .sanitized.md.
    """
    try:
        output_path = apply_title_changes_from_work(
            work_id=work_id,
            source_key=request.source_key,
            force=request.force,
            verbose=False
        )
        
        return ApplyTitleChangesResponse(
            success=True,
            output_path=str(output_path),
            message=f"Title changes applied successfully to {output_path.name}"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {str(e)}. Use force=true to proceed anyway."
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply title changes: {str(e)}"
        )


@router.post(
    "/work/{work_id}/skip-apply",
    response_model=SkipApplyResponse,
    summary="Skip sanitization",
    description="Skip title changes and copy original markdown to sanitized version.",
)
async def skip_apply_endpoint(
    work_id: int,
    request: SkipApplyRequest
) -> SkipApplyResponse:
    """
    Skip sanitization and copy original to sanitized.
    
    Useful when the document doesn't need heading corrections.
    """
    try:
        output_path = skip_apply_from_work(
            work_id=work_id,
            source_key=request.source_key,
            force=request.force,
            verbose=False
        )
        
        return SkipApplyResponse(
            success=True,
            output_path=str(output_path),
            message=f"Original copied to sanitized: {output_path.name}"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {str(e)}. Use force=true to proceed anyway."
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to skip-apply: {str(e)}"
        )


@router.get(
    "/work/{work_id}/prompt",
    response_model=PromptForWorkResponse,
    summary="Get LLM prompt for title changes",
    description="Build and return the LLM prompt for suggesting title changes without executing it.",
)
async def get_prompt_for_work(
    work_id: int,
    source_key: str = "original_markdown",
    force: bool = False
) -> PromptForWorkResponse:
    """
    Get the LLM prompt for suggesting title changes.
    
    This endpoint builds the prompt that would be sent to the LLM, allowing
    manual execution in an external LLM interface or inspection before running.
    """
    try:
        result = build_prompt_for_work(
            work_id=work_id,
            source_key=source_key,
            force=force
        )
        
        return PromptForWorkResponse(
            prompt=result["prompt"],
            work_title=result["work_title"],
            work_authors=result["work_authors"]
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HashMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hash mismatch: {str(e)}. Use force=true to proceed anyway."
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build prompt: {str(e)}"
        )


@router.post(
    "/work/{work_id}/manual-title-changes",
    response_model=ManualTitleChangesResponse,
    summary="Save manually generated title changes",
    description="Save title changes from a manually executed LLM response.",
)
async def save_manual_title_changes(
    work_id: int,
    request: ManualTitleChangesRequest
) -> ManualTitleChangesResponse:
    """
    Save title changes from a manual LLM response.
    
    Takes the raw response text from a manually executed LLM prompt and
    processes it to create a title_changes file, updating the database.
    """
    try:
        output_path = save_title_changes_from_response(
            work_id=work_id,
            source_key=request.source_key,
            llm_response=request.llm_response,
            force=request.force
        )
        
        return ManualTitleChangesResponse(
            success=True,
            output_path=str(output_path),
            message=f"Title changes saved successfully to {output_path.name}"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save title changes: {str(e)}"
        )


@router.get(
    "/work/{work_id}/titles/content",
    response_model=TitlesContentResponse,
    summary="Get titles file content",
    description="Retrieve the content of a work's titles file for viewing/editing.",
)
async def get_titles_content(work_id: int) -> TitlesContentResponse:
    """
    Get the content of a work's titles file.
    
    Retrieves the raw markdown content from the titles file referenced
    in work.files["titles"].
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "titles" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have a titles file"
            )
        
        titles_info = work.files["titles"]
        titles_path = Path(titles_info["path"])
        
        if not titles_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Titles file not found on disk: {titles_path}"
            )
        
        # Read file content
        try:
            content = titles_path.read_text(encoding="utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read titles file: {str(e)}"
            )
        
        # Get current hash
        current_hash = compute_file_hash(titles_path)
        
        return TitlesContentResponse(
            content=content,
            filename=titles_path.name,
            hash=current_hash
        )


@router.put(
    "/work/{work_id}/titles/content",
    response_model=TitlesContentResponse,
    summary="Update titles file content",
    description="Update the content of a work's titles file and update its hash.",
)
async def update_titles_content(
    work_id: int,
    request: UpdateTitlesContentRequest
) -> TitlesContentResponse:
    """
    Update the content of a work's titles file.
    
    Writes the new content to the file, computes a new hash, and updates
    the work.files["titles"]["hash"] in the database.
    """
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work with ID {work_id} not found"
            )
        
        if not work.files or "titles" not in work.files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work {work_id} does not have a titles file"
            )
        
        titles_info = work.files["titles"]
        titles_path = Path(titles_info["path"])
        
        if not titles_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Titles file not found on disk: {titles_path}"
            )
        
        # Make file writable
        try:
            set_file_writable(titles_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to make file writable: {str(e)}"
            )
        
        # Write new content
        try:
            titles_path.write_text(request.content, encoding="utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to write file: {str(e)}"
            )
        
        # Make file read-only again
        try:
            set_file_readonly(titles_path)
        except Exception as e:
            # Not critical, log but continue
            print(f"Warning: Failed to set file read-only: {e}")
        
        # Compute new hash of the titles file
        new_hash = compute_file_hash(titles_path)
        
        # Update work.files with new hash
        # Must create a new dict to trigger SQLAlchemy's change detection for JSON columns
        updated_files = dict(work.files) if work.files else {}
        updated_files["titles"] = {
            "path": str(titles_path.resolve()),
            "hash": new_hash
        }
        work.files = updated_files
        
        session.commit()
        session.refresh(work)
        
        return TitlesContentResponse(
            content=request.content,
            filename=titles_path.name,
            hash=new_hash
        )


# Legacy endpoints (kept for backwards compatibility)

@router.post(
    "/extract-toc",
    response_model=ExtractTOCResponse,
    summary="Extract table of contents (legacy)",
    description="Extract the table of contents from a markdown document.",
)
async def extract_toc(request: ExtractTOCRequest) -> ExtractTOCResponse:
    """
    Extract table of contents from markdown.
    
    Legacy endpoint - consider using work-based endpoints instead.
    """
    # TODO: Implement using psychrag.sanitization.extract_toc
    return ExtractTOCResponse(
        toc_entries=[
            {"level": 1, "title": "Introduction", "line": 1},
            {"level": 2, "title": "Background", "line": 25},
            {"level": 2, "title": "Methods", "line": 100},
        ],
        total_entries=3,
        message="Stub: TOC extraction",
    )


@router.post(
    "/extract-titles",
    response_model=ExtractTitlesResponse,
    summary="Extract titles (legacy)",
    description="Extract all heading titles from a markdown document.",
)
async def extract_titles(request: ExtractTitlesRequest) -> ExtractTitlesResponse:
    """
    Extract all titles/headings from markdown.
    
    Legacy endpoint - consider using work-based endpoints instead.
    """
    # TODO: Implement using psychrag.sanitization.extract_titles
    return ExtractTitlesResponse(
        titles=[
            {"level": 1, "title": "Chapter 1: Introduction", "original_line": 1},
            {"level": 2, "title": "1.1 Background", "original_line": 25},
        ],
        total_count=2,
    )


@router.post(
    "/suggest-changes",
    response_model=SuggestChangesResponse,
    summary="Suggest heading changes (legacy)",
    description="Use LLM to suggest improvements to heading structure.",
)
async def suggest_changes(request: SuggestChangesRequest) -> SuggestChangesResponse:
    """
    Get AI-suggested heading improvements.
    
    Legacy endpoint - consider using work-based endpoints instead.
    """
    # TODO: Implement using psychrag.sanitization.suggest_heading_changes
    return SuggestChangesResponse(
        suggestions=[
            {
                "original": "CHAPTER 1: INTRODUCTION",
                "suggested": "Chapter 1: Introduction",
                "reason": "Normalize capitalization",
                "line": 1,
            },
        ],
        total_suggestions=1,
        confidence=0.85,
    )


@router.post(
    "/apply-changes",
    response_model=ApplyChangesResponse,
    status_code=status.HTTP_200_OK,
    summary="Apply heading changes (legacy)",
    description="Apply approved heading changes to the document.",
)
async def apply_changes(request: ApplyChangesRequest) -> ApplyChangesResponse:
    """
    Apply heading changes to document.
    
    Legacy endpoint - consider using work-based endpoints instead.
    """
    # TODO: Implement using psychrag.sanitization.apply_title_changes
    return ApplyChangesResponse(
        success=True,
        changes_applied=len(request.changes),
        backup_path="/output/backup/document_backup.md",
        message=f"Stub: Would apply {len(request.changes)} changes",
    )
