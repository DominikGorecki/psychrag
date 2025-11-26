"""
RAG Router - Retrieval, Augmentation and Generation operations.

Endpoints for query management:
    GET  /rag/queries                      - List all queries with status info
    GET  /rag/queries/{id}                 - Get single query details
    POST /rag/queries/{id}/embed           - Run vectorization
    POST /rag/queries/{id}/retrieve        - Run retrieval
    POST /rag/queries/{id}/consolidate     - Run consolidation
    GET  /rag/queries/{id}/augment/prompt  - Get augmented prompt
    POST /rag/queries/{id}/augment/run     - Run augmented prompt with LLM
    POST /rag/queries/{id}/augment/manual  - Save manually-run LLM response

Endpoints for query expansion:
    POST /rag/expansion/prompt             - Generate expansion prompt (no LLM)
    POST /rag/expansion/run                - Run full expansion with LLM
    POST /rag/expansion/manual             - Parse & save manual expansion response
"""

from fastapi import APIRouter, HTTPException, status

from psychrag.data.database import get_session
from psychrag.data.models import Query, Result
from psychrag.retrieval import (
    vectorize_query,
    generate_expansion_prompt,
    parse_expansion_response,
    save_expansion_to_db,
    expand_query,
    retrieve,
)
from psychrag.augmentation import consolidate_context, generate_augmented_prompt
from psychrag.ai.config import ModelTier
from psychrag.ai.llm_factory import create_langchain_chat

from psychrag_api.schemas.rag_queries import (
    QueryListItem,
    QueryListResponse,
    QueryDetailResponse,
    ExpansionPromptRequest,
    ExpansionPromptResponse,
    ExpansionRunRequest,
    ExpansionRunResponse,
    ExpansionManualRequest,
    ExpansionManualResponse,
    EmbedResponse,
    RetrieveOperationResponse,
    ConsolidateResponse,
    AugmentPromptResponse,
    AugmentRunRequest,
    AugmentRunResponse,
    AugmentManualRequest,
    AugmentManualResponse,
)

router = APIRouter()


def _get_query_status(query: Query) -> str:
    """Determine the current status of a query."""
    if query.vector_status == "to_vec":
        return "needs_embeddings"
    if not query.retrieved_context:
        return "needs_retrieval"
    if not query.clean_retrieval_context:
        return "needs_consolidation"
    return "ready"


# ============================================================================
# Query Listing Endpoints
# ============================================================================

@router.get(
    "/queries",
    response_model=QueryListResponse,
    summary="List all queries",
    description="List all queries with their current status.",
)
async def list_queries() -> QueryListResponse:
    """List all queries with status information."""
    with get_session() as session:
        queries = session.query(Query).order_by(Query.created_at.desc()).all()

        items = []
        for q in queries:
            items.append(QueryListItem(
                id=q.id,
                original_query=q.original_query,
                created_at=q.created_at,
                status=_get_query_status(q),
                intent=q.intent,
                entities_count=len(q.entities) if q.entities else 0
            ))

        return QueryListResponse(queries=items, total=len(items))


@router.get(
    "/queries/{query_id}",
    response_model=QueryDetailResponse,
    summary="Get query details",
    description="Get detailed information about a specific query.",
)
async def get_query(query_id: int) -> QueryDetailResponse:
    """Get detailed query information."""
    with get_session() as session:
        query = session.query(Query).filter(Query.id == query_id).first()

        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with ID {query_id} not found"
            )

        return QueryDetailResponse(
            id=query.id,
            original_query=query.original_query,
            expanded_queries=query.expanded_queries,
            hyde_answer=query.hyde_answer,
            intent=query.intent,
            entities=query.entities,
            vector_status=query.vector_status,
            has_retrieved_context=bool(query.retrieved_context),
            has_clean_context=bool(query.clean_retrieval_context),
            created_at=query.created_at,
            updated_at=query.updated_at
        )


# ============================================================================
# Query Operations Endpoints
# ============================================================================

@router.post(
    "/queries/{query_id}/embed",
    response_model=EmbedResponse,
    summary="Embed query vectors",
    description="Generate embeddings for a query.",
)
async def embed_query(query_id: int) -> EmbedResponse:
    """Generate embeddings for a query."""
    try:
        result = vectorize_query(query_id=query_id, verbose=False)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Vectorization failed"
            )

        return EmbedResponse(
            query_id=result.query_id,
            total_embeddings=result.total_embeddings,
            original_count=result.original_count,
            mqe_count=result.mqe_count,
            hyde_count=result.hyde_count,
            success=True,
            message="Embeddings generated successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/queries/{query_id}/retrieve",
    response_model=RetrieveOperationResponse,
    summary="Run retrieval",
    description="Run dense + lexical retrieval with RRF fusion and reranking.",
)
async def retrieve_query(query_id: int) -> RetrieveOperationResponse:
    """Run retrieval for a query."""
    try:
        result = retrieve(query_id=query_id, verbose=False)

        return RetrieveOperationResponse(
            query_id=result.query_id,
            total_dense_candidates=result.total_dense_candidates,
            total_lexical_candidates=result.total_lexical_candidates,
            rrf_candidates=result.rrf_candidates,
            final_count=result.final_count,
            message=f"Retrieved {result.final_count} chunks"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/queries/{query_id}/consolidate",
    response_model=ConsolidateResponse,
    summary="Run consolidation",
    description="Consolidate retrieved context by grouping and merging chunks.",
)
async def consolidate_query(query_id: int) -> ConsolidateResponse:
    """Run consolidation for a query."""
    try:
        result = consolidate_context(query_id=query_id, verbose=False)

        return ConsolidateResponse(
            query_id=result.query_id,
            original_count=result.original_count,
            consolidated_count=result.consolidated_count,
            message=f"Consolidated {result.original_count} items into {result.consolidated_count} groups"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


# ============================================================================
# Augmentation Endpoints
# ============================================================================

@router.get(
    "/queries/{query_id}/augment/prompt",
    response_model=AugmentPromptResponse,
    summary="Get augmented prompt",
    description="Get the full augmented RAG prompt for a query.",
)
async def get_augment_prompt(query_id: int, top_n: int = 5) -> AugmentPromptResponse:
    """Get the augmented prompt for a query."""
    try:
        prompt = generate_augmented_prompt(query_id=query_id, top_n=top_n)

        with get_session() as session:
            query = session.query(Query).filter(Query.id == query_id).first()
            context_count = len(query.clean_retrieval_context or [])

            return AugmentPromptResponse(
                query_id=query_id,
                original_query=query.original_query,
                prompt=prompt,
                context_count=min(context_count, top_n)
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/queries/{query_id}/augment/run",
    response_model=AugmentRunResponse,
    summary="Run augmented prompt",
    description="Run the augmented prompt with LLM and save result.",
)
async def run_augment(
    query_id: int,
    request: AugmentRunRequest = AugmentRunRequest()
) -> AugmentRunResponse:
    """Run augmented prompt with LLM and save result."""
    try:
        # Generate the prompt
        prompt = generate_augmented_prompt(query_id=query_id, top_n=5)

        # Create LangChain chat with FULL model and search
        stack = create_langchain_chat(tier=ModelTier.FULL, search=True, temperature=0.2)

        # Call LLM
        response = stack.chat.invoke(prompt)
        response_text = response.content

        # Save result to database
        with get_session() as session:
            result = Result(
                query_id=query_id,
                response_text=response_text
            )
            session.add(result)
            session.commit()
            result_id = result.id

        return AugmentRunResponse(
            query_id=query_id,
            result_id=result_id,
            response_text=response_text,
            message="Augmented prompt executed and result saved"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/queries/{query_id}/augment/manual",
    response_model=AugmentManualResponse,
    summary="Save manual augmented response",
    description="Save a manually-run LLM response for an augmented prompt.",
)
async def save_manual_augment(
    query_id: int,
    request: AugmentManualRequest
) -> AugmentManualResponse:
    """Save manually-run augmented response."""
    with get_session() as session:
        # Verify query exists
        query = session.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with ID {query_id} not found"
            )

        # Save result
        result = Result(
            query_id=query_id,
            response_text=request.response_text
        )
        session.add(result)
        session.commit()

        return AugmentManualResponse(
            query_id=query_id,
            result_id=result.id,
            message="Manual response saved successfully"
        )


# ============================================================================
# Query Expansion Endpoints
# ============================================================================

@router.post(
    "/expansion/prompt",
    response_model=ExpansionPromptResponse,
    summary="Generate expansion prompt",
    description="Generate the expansion prompt without calling LLM.",
)
async def get_expansion_prompt(request: ExpansionPromptRequest) -> ExpansionPromptResponse:
    """Generate expansion prompt for manual LLM execution."""
    prompt = generate_expansion_prompt(query=request.query, n=request.n)

    return ExpansionPromptResponse(
        prompt=prompt,
        query=request.query,
        n=request.n
    )


@router.post(
    "/expansion/run",
    response_model=ExpansionRunResponse,
    summary="Run query expansion",
    description="Run full query expansion with LLM.",
)
async def run_expansion(request: ExpansionRunRequest) -> ExpansionRunResponse:
    """Run full query expansion pipeline."""
    try:
        result = expand_query(query=request.query, n=request.n, verbose=False)

        return ExpansionRunResponse(
            query_id=result.query_id,
            original_query=result.original_query,
            expanded_queries=result.expanded_queries,
            hyde_answer=result.hyde_answer,
            intent=result.intent,
            entities=result.entities,
            message="Query expanded and saved successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/expansion/manual",
    response_model=ExpansionManualResponse,
    summary="Save manual expansion",
    description="Parse and save manually-run expansion response.",
)
async def save_manual_expansion(request: ExpansionManualRequest) -> ExpansionManualResponse:
    """Parse and save manually-run expansion response."""
    try:
        # Parse the response
        parsed = parse_expansion_response(request.response_text)

        # Save to database
        query_id = save_expansion_to_db(request.query, parsed)

        return ExpansionManualResponse(
            query_id=query_id,
            message="Expansion parsed and saved successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
