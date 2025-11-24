"""
Retrieval module for dense + lexical search with RRF fusion and BGE reranking.

This module implements the full retrieval pipeline:
1. Dense retrieval (pgvector similarity)
2. Lexical retrieval (PostgreSQL full-text search)
3. RRF fusion
4. BGE reranking with entity/intent bias
5. Final selection and storage

Usage:
    from psychrag.retrieval.retrieve import retrieve
    result = retrieve(query_id=1, verbose=True)
"""

from dataclasses import dataclass, field
from pathlib import Path

import torch
from sqlalchemy import text
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from psychrag.data.database import get_session
from psychrag.data.models import Chunk, Query, Work
from psychrag.utils.file_utils import compute_file_hash


@dataclass
class RetrievedChunk:
    """A retrieved chunk with all metadata and scores."""

    id: int
    parent_id: int | None
    work_id: int
    content: str
    enriched_content: str
    start_line: int
    end_line: int
    level: str
    dense_rank: int | None = None
    lexical_rank: int | None = None
    rrf_score: float = 0.0
    rerank_score: float = 0.0
    entity_boost: float = 0.0
    final_score: float = 0.0


@dataclass
class RetrievalResult:
    """Result of the retrieval operation."""

    query_id: int
    total_dense_candidates: int
    total_lexical_candidates: int
    rrf_candidates: int
    final_count: int
    chunks: list[RetrievedChunk]


# Default parameters
DEFAULT_DENSE_LIMIT = 15
DEFAULT_LEXICAL_LIMIT = 10
DEFAULT_RRF_K = 60
DEFAULT_TOP_K_RRF = 60
DEFAULT_TOP_N_FINAL = 12
DEFAULT_ENTITY_BOOST = 0.05
DEFAULT_MIN_CONTENT_LENGTH = 350    #character
DEFAULT_CONTEXT_SENTENCES = 5


def _dense_search(
    session,
    embedding: list,
    limit: int = DEFAULT_DENSE_LIMIT
) -> list[tuple[int, int]]:
    """Perform dense vector search.

    Returns list of (chunk_id, rank) tuples.
    """
    # Convert to list if numpy array, then format as PostgreSQL vector literal
    if hasattr(embedding, 'tolist'):
        embedding = embedding.tolist()
    embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'

    result = session.execute(
        text("""
            SELECT id
            FROM chunks
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :embedding
            LIMIT :limit
        """),
        {"embedding": embedding_str, "limit": limit}
    )
    return [(row[0], i + 1) for i, row in enumerate(result.fetchall())]


def _lexical_search(
    session,
    query_text: str,
    limit: int = DEFAULT_LEXICAL_LIMIT
) -> list[tuple[int, int]]:
    """Perform lexical full-text search.

    Returns list of (chunk_id, rank) tuples.
    """
    # Convert query to tsquery format
    result = session.execute(
        text("""
            SELECT id
            FROM chunks
            WHERE content_tsvector @@ plainto_tsquery('english', :query)
            ORDER BY ts_rank(content_tsvector, plainto_tsquery('english', :query)) DESC
            LIMIT :limit
        """),
        {"query": query_text, "limit": limit}
    )
    return [(row[0], i + 1) for i, row in enumerate(result.fetchall())]


def _compute_rrf_scores(
    results_list: list[list[tuple[int, int]]],
    k: int = DEFAULT_RRF_K
) -> dict[int, float]:
    """Compute RRF scores from multiple ranked lists.

    Args:
        results_list: List of [(chunk_id, rank), ...] for each query
        k: RRF constant (default 60)

    Returns:
        Dict mapping chunk_id to RRF score
    """
    scores = {}
    for results in results_list:
        for chunk_id, rank in results:
            if chunk_id not in scores:
                scores[chunk_id] = 0.0
            scores[chunk_id] += 1.0 / (k + rank)
    return scores


def _enrich_content(
    chunk: Chunk,
    work: Work,
    context_sentences: int = DEFAULT_CONTEXT_SENTENCES,
    min_length: int = DEFAULT_MIN_CONTENT_LENGTH
) -> str:
    """Enrich short chunks with surrounding context from markdown file.

    Args:
        chunk: The chunk to potentially enrich
        work: The work containing markdown_path
        context_sentences: Number of sentences to add above/below
        min_length: Minimum content length before enrichment

    Returns:
        Enriched content or original content
    """
    if len(chunk.content) >= min_length:
        return chunk.content

    if not work.markdown_path:
        return chunk.content

    markdown_path = Path(work.markdown_path)
    if not markdown_path.exists():
        return chunk.content

    # Verify file hasn't changed
    if work.content_hash:
        current_hash = compute_file_hash(markdown_path)
        if current_hash != work.content_hash:
            return chunk.content

    # Read markdown file
    try:
        lines = markdown_path.read_text(encoding='utf-8').splitlines()
    except Exception:
        return chunk.content

    # Get context lines (0-indexed)
    start_idx = max(0, chunk.start_line - 1 - context_sentences)
    end_idx = min(len(lines), chunk.end_line + context_sentences)

    # Build enriched content
    above_lines = lines[start_idx:chunk.start_line - 1] if chunk.start_line > 1 else []
    below_lines = lines[chunk.end_line:end_idx] if chunk.end_line < len(lines) else []

    parts = []
    if above_lines:
        parts.append('\n'.join(above_lines))
        parts.append('')  # Blank line
    parts.append(chunk.content)
    if below_lines:
        parts.append('')  # Blank line
        parts.append('\n'.join(below_lines))

    return '\n'.join(parts)


def _load_reranker():
    """Load BGE reranker model with GPU fallback to CPU."""
    model_name = "BAAI/bge-reranker-large"

    # Try GPU first
    device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    if device == "cuda":
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            torch_dtype=torch.float16
        ).to(device)
    else:
        model = AutoModelForSequenceClassification.from_pretrained(model_name).to(device)

    model.eval()
    return tokenizer, model, device


def _rerank_chunks(
    query: str,
    chunks: list[RetrievedChunk],
    batch_size: int = 8,
    max_length: int = 512
) -> list[RetrievedChunk]:
    """Rerank chunks using BGE reranker.

    Args:
        query: Original query text
        chunks: List of chunks to rerank
        batch_size: Batch size for inference
        max_length: Maximum token length

    Returns:
        Chunks with updated rerank_score
    """
    if not chunks:
        return chunks

    tokenizer, model, device = _load_reranker()

    # Prepare pairs
    pairs = [(query, chunk.enriched_content) for chunk in chunks]

    # Process in batches
    scores = []
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i:i + batch_size]

        inputs = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            batch_scores = outputs.logits.squeeze(-1).cpu().tolist()

            # Handle single item case
            if isinstance(batch_scores, float):
                batch_scores = [batch_scores]

            scores.extend(batch_scores)

    # Update chunks with scores
    for chunk, score in zip(chunks, scores):
        chunk.rerank_score = score

    return chunks


def _apply_entity_bias(
    chunks: list[RetrievedChunk],
    entities: list[str],
    boost: float = DEFAULT_ENTITY_BOOST
) -> list[RetrievedChunk]:
    """Apply entity boost to rerank scores.

    Args:
        chunks: Chunks with rerank scores
        entities: List of entities to match
        boost: Score boost per entity match

    Returns:
        Chunks with updated entity_boost and final_score
    """
    if not entities:
        for chunk in chunks:
            chunk.final_score = chunk.rerank_score
        return chunks

    # Normalize entities for matching
    normalized_entities = [e.lower() for e in entities]

    for chunk in chunks:
        content_lower = chunk.enriched_content.lower()

        # Count entity matches
        matches = sum(1 for entity in normalized_entities if entity in content_lower)

        chunk.entity_boost = matches * boost
        chunk.final_score = chunk.rerank_score + chunk.entity_boost

    return chunks


def _apply_intent_bias(
    chunks: list[RetrievedChunk],
    intent: str | None
) -> list[RetrievedChunk]:
    """Apply intent-based bias to scores.

    Currently a placeholder that does nothing.
    Future implementation will adjust scores based on intent type.

    Args:
        chunks: Chunks with current scores
        intent: Query intent type

    Returns:
        Chunks (unmodified for now)
    """
    # Placeholder - will implement intent-specific biasing later
    return chunks


def retrieve(
    query_id: int,
    dense_limit: int = DEFAULT_DENSE_LIMIT,
    lexical_limit: int = DEFAULT_LEXICAL_LIMIT,
    rrf_k: int = DEFAULT_RRF_K,
    top_k_rrf: int = DEFAULT_TOP_K_RRF,
    top_n_final: int = DEFAULT_TOP_N_FINAL,
    entity_boost: float = DEFAULT_ENTITY_BOOST,
    verbose: bool = False
) -> RetrievalResult:
    """Perform full retrieval pipeline for a query.

    Args:
        query_id: ID of the Query in the database
        dense_limit: Max results per dense query (default 15)
        lexical_limit: Max results per lexical query (default 10)
        rrf_k: RRF constant (default 60)
        top_k_rrf: Top candidates after RRF (default 60)
        top_n_final: Final number of results (default 12)
        entity_boost: Score boost per entity match (default 0.05)
        verbose: Print progress information

    Returns:
        RetrievalResult with retrieved chunks

    Raises:
        ValueError: If query not found or not vectorized
    """
    with get_session() as session:
        # Fetch query
        query = session.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise ValueError(f"Query with ID {query_id} not found")

        if query.vector_status != 'vec':
            raise ValueError(f"Query {query_id} has not been vectorized (status: {query.vector_status})")

        if verbose:
            print(f"Retrieving for query {query_id}: {query.original_query[:50]}...")

        # Collect all embeddings
        embeddings = []
        query_texts = []

        # Original query
        if query.embedding_original is not None:
            embeddings.append(query.embedding_original)
        query_texts.append(query.original_query)

        # MQE queries
        mqe_embeddings = query.embeddings_mqe or []
        mqe_texts = query.expanded_queries or []
        embeddings.extend(mqe_embeddings)
        query_texts.extend(mqe_texts)

        # HyDE (only for dense, not lexical)
        if query.embedding_hyde is not None:
            embeddings.append(query.embedding_hyde)

        if verbose:
            print(f"  Using {len(embeddings)} embeddings for dense search")
            print(f"  Using {len(query_texts)} queries for lexical search")

        # Dense retrieval
        dense_results = []
        for emb in embeddings:
            results = _dense_search(session, emb, dense_limit)
            dense_results.append(results)

        total_dense = sum(len(r) for r in dense_results)
        if verbose:
            print(f"  Dense retrieval: {total_dense} candidates")

        # Lexical retrieval (not using HyDE)
        lexical_results = []
        for text in query_texts:
            results = _lexical_search(session, text, lexical_limit)
            lexical_results.append(results)

        total_lexical = sum(len(r) for r in lexical_results)
        if verbose:
            print(f"  Lexical retrieval: {total_lexical} candidates")

        # RRF fusion
        all_results = dense_results + lexical_results
        rrf_scores = _compute_rrf_scores(all_results, rrf_k)

        # Sort by RRF score and take top_k_rrf
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        top_ids = sorted_ids[:top_k_rrf]

        if verbose:
            print(f"  RRF fusion: {len(rrf_scores)} unique candidates -> top {len(top_ids)}")

        # Fetch chunk data
        chunks_data = session.query(Chunk).filter(Chunk.id.in_(top_ids)).all()
        chunks_map = {c.id: c for c in chunks_data}

        # Get work data for enrichment
        work_ids = {c.work_id for c in chunks_data}
        works = session.query(Work).filter(Work.id.in_(work_ids)).all()
        works_map = {w.id: w for w in works}

        # Build RetrievedChunk objects
        retrieved_chunks = []
        for chunk_id in top_ids:
            if chunk_id not in chunks_map:
                continue

            chunk = chunks_map[chunk_id]
            work = works_map.get(chunk.work_id)

            # Enrich content
            enriched = _enrich_content(chunk, work) if work else chunk.content

            retrieved_chunks.append(RetrievedChunk(
                id=chunk.id,
                parent_id=chunk.parent_id,
                work_id=chunk.work_id,
                content=chunk.content,
                enriched_content=enriched,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                level=chunk.level,
                rrf_score=rrf_scores[chunk_id]
            ))

        if verbose:
            print(f"  Reranking {len(retrieved_chunks)} candidates...")

        # BGE reranking
        retrieved_chunks = _rerank_chunks(query.original_query, retrieved_chunks)

        # Apply entity bias
        entities = query.entities or []
        retrieved_chunks = _apply_entity_bias(retrieved_chunks, entities, entity_boost)

        # Apply intent bias (placeholder)
        retrieved_chunks = _apply_intent_bias(retrieved_chunks, query.intent)

        # Final sort and selection
        retrieved_chunks.sort(key=lambda x: x.final_score, reverse=True)
        final_chunks = retrieved_chunks[:top_n_final]

        if verbose:
            print(f"  Final selection: {len(final_chunks)} chunks")

        # Save to database
        context_data = []
        for chunk in final_chunks:
            context_data.append({
                "id": chunk.id,
                "parent_id": chunk.parent_id,
                "work_id": chunk.work_id,
                "content": chunk.content,
                "enriched_content": chunk.enriched_content,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "level": chunk.level,
                "rrf_score": chunk.rrf_score,
                "rerank_score": chunk.rerank_score,
                "entity_boost": chunk.entity_boost,
                "final_score": chunk.final_score
            })

        query.retrieved_context = context_data
        session.commit()

        if verbose:
            print(f"  Saved {len(context_data)} results to query.retrieved_context")

        return RetrievalResult(
            query_id=query_id,
            total_dense_candidates=total_dense,
            total_lexical_candidates=total_lexical,
            rrf_candidates=len(rrf_scores),
            final_count=len(final_chunks),
            chunks=final_chunks
        )
