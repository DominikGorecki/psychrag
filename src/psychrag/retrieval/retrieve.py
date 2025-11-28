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

import numpy as np
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
    heading_breadcrumbs: str | None = None
    dense_rank: int | None = None
    lexical_rank: int | None = None
    rrf_score: float = 0.0
    rerank_score: float = 0.0
    entity_boost: float = 0.0
    final_score: float = 0.0
    # Embedding for MMR diversity (not persisted, used internally)
    _embedding: np.ndarray | None = field(default=None, repr=False)


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
DEFAULT_DENSE_LIMIT = 19
DEFAULT_LEXICAL_LIMIT = 5
DEFAULT_RRF_K = 50                  #60
DEFAULT_TOP_K_RRF = 75              #60
DEFAULT_TOP_N_FINAL = 17
DEFAULT_ENTITY_BOOST = 0.05   #0.05
DEFAULT_MIN_CONTENT_LENGTH = 750    # characters (for enrichment)
DEFAULT_ENRICH_LINES_ABOVE = 0      # lines to add above chunk when enriching
DEFAULT_ENRICH_LINES_BELOW = 13     # lines to add below chunk when enriching
DEFAULT_MIN_WORD_COUNT = 150         # minimum words in chunk.content to be included
DEFAULT_MIN_CHAR_COUNT = 250        # minimum characters in chunk.content to be included
# Default MMR parameters
DEFAULT_MMR_LAMBDA = 0.7  #0.7 Balance between relevance (1.0) and diversity (0.0)


def _meets_minimum_requirements(
    content: str,
    min_word_count: int = DEFAULT_MIN_WORD_COUNT,
    min_char_count: int = DEFAULT_MIN_CHAR_COUNT
) -> bool:
    """Check if chunk content meets minimum length requirements.

    Args:
        content: The chunk content to check
        min_word_count: Minimum number of words required (0 to disable)
        min_char_count: Minimum number of characters required (0 to disable)

    Returns:
        True if content meets both requirements, False otherwise
    """
    if not content or not content.strip():
        return False

    # Check character count (if enabled)
    if min_char_count > 0 and len(content) < min_char_count:
        return False

    # Check word count (if enabled)
    if min_word_count > 0:
        word_count = len(content.split())
        if word_count < min_word_count:
            return False

    return True


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
    """Perform lexical full-text search with phrase support.

    Uses websearch_to_tsquery for better phrase handling:
    - Quoted phrases ("schema therapy") require adjacent words
    - Negation (-anxiety) excludes matching chunks
    - OR logic (CBT or DBT) matches either term

    Uses ts_rank_cd which considers document structure and proximity,
    providing better ranking than basic ts_rank.

    Returns list of (chunk_id, rank) tuples.
    """
    # Use websearch_to_tsquery for phrase and negation support
    # ts_rank_cd considers cover density (proximity) for better ranking
    result = session.execute(
        text("""
            SELECT id
            FROM chunks
            WHERE content_tsvector @@ websearch_to_tsquery('english', :query)
                AND vector_status = 'vec'
            ORDER BY ts_rank_cd(content_tsvector, websearch_to_tsquery('english', :query)) DESC
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
    lines_above: int = DEFAULT_ENRICH_LINES_ABOVE,
    lines_below: int = DEFAULT_ENRICH_LINES_BELOW,
    min_length: int = DEFAULT_MIN_CONTENT_LENGTH
) -> str:
    """Enrich short chunks with surrounding context from markdown file.

    Args:
        chunk: The chunk to potentially enrich
        work: The work containing markdown_path
        lines_above: Number of lines to add above chunk (default 0)
        lines_below: Number of lines to add below chunk (default 13)
        min_length: Minimum content length before enrichment (default 350)

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
    start_idx = max(0, chunk.start_line - 1 - lines_above)
    end_idx = min(len(lines), chunk.end_line + lines_below)

    # Build enriched content
    above_lines = lines[start_idx:chunk.start_line - 1] if lines_above > 0 and chunk.start_line > 1 else []
    below_lines = lines[chunk.end_line:end_idx] if lines_below > 0 and chunk.end_line < len(lines) else []

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


# Intent preferences: level preferences and length preferences per intent type
# Each intent maps to preferred heading levels and content length category
INTENT_PREFERENCES = {
    "DEFINITION": {
        "preferred_levels": ["H2", "H3"],
        "length_preference": "short",  # < 500 chars
        "level_boost": 0.03,
        "length_boost": 0.01,
    },
    "MECHANISM": {
        "preferred_levels": ["H3", "H4", "chunk"],
        "length_preference": "long",  # > 800 chars
        "level_boost": 0.02,
        "length_boost": 0.01,
    },
    "COMPARISON": {
        "preferred_levels": ["H2", "H3"],
        "length_preference": "medium",  # 400-900 chars
        "level_boost": 0.02,
        "length_boost": 0.01,
    },
    "APPLICATION": {
        "preferred_levels": ["H4", "chunk", "sentence"],
        "length_preference": "medium",
        "level_boost": 0.02,
        "length_boost": 0.01,
    },
    "STUDY_DETAIL": {
        "preferred_levels": ["H4", "chunk"],
        "length_preference": "long",
        "level_boost": 0.03,
        "length_boost": 0.01,
    },
    "CRITIQUE": {
        "preferred_levels": ["H3", "H4"],
        "length_preference": "medium",
        "level_boost": 0.02,
        "length_boost": 0.01,
    },
}


def _apply_intent_bias(
    chunks: list[RetrievedChunk],
    intent: str | None
) -> list[RetrievedChunk]:
    """Apply intent-based bias to scores.

    Different intents favor different chunk characteristics:
    - DEFINITION: prefer shorter chunks at H2/H3 level
    - MECHANISM: prefer longer explanatory chunks at H3/H4/chunk level
    - COMPARISON: prefer H2/H3 chunks with medium length
    - APPLICATION: prefer practical H4/chunk/sentence with medium length
    - STUDY_DETAIL: prefer longer H4/chunk with methodology details
    - CRITIQUE: prefer H3/H4 chunks with evaluative content

    Args:
        chunks: Chunks with current final_score set
        intent: Query intent type (DEFINITION, MECHANISM, etc.)

    Returns:
        Chunks with final_score adjusted based on intent preferences
    """
    if not intent or not chunks:
        return chunks

    # Get preferences for this intent
    prefs = INTENT_PREFERENCES.get(intent.upper())
    if not prefs:
        return chunks

    for chunk in chunks:
        boost = 0.0

        # Level preference boost
        if chunk.level in prefs["preferred_levels"]:
            boost += prefs["level_boost"]

        # Length preference boost (based on enriched_content)
        content_len = len(chunk.enriched_content)
        length_pref = prefs["length_preference"]

        if length_pref == "short" and content_len < 500:
            boost += prefs["length_boost"]
        elif length_pref == "long" and content_len > 800:
            boost += prefs["length_boost"]
        elif length_pref == "medium" and 400 <= content_len <= 900:
            boost += prefs["length_boost"]

        # Apply the boost to final_score
        chunk.final_score += boost

    return chunks




def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score between -1 and 1
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def _jaccard_similarity(text1: str, text2: str) -> float:
    """Compute Jaccard similarity based on word overlap.

    Used as fallback when embeddings are not available.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Jaccard similarity score between 0 and 1
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union if union > 0 else 0.0


def _compute_chunk_similarity(
    chunk1: RetrievedChunk,
    chunk2: RetrievedChunk
) -> float:
    """Compute similarity between two chunks.

    Uses embedding cosine similarity if both chunks have embeddings,
    otherwise falls back to Jaccard word overlap.

    Args:
        chunk1: First chunk
        chunk2: Second chunk

    Returns:
        Similarity score between 0 and 1
    """
    # Use embedding similarity if available
    if chunk1._embedding is not None and chunk2._embedding is not None:
        # Cosine similarity can be negative; normalize to [0, 1]
        cos_sim = _cosine_similarity(chunk1._embedding, chunk2._embedding)
        return (cos_sim + 1) / 2  # Map [-1, 1] to [0, 1]

    # Fallback to Jaccard
    return _jaccard_similarity(chunk1.enriched_content, chunk2.enriched_content)


def _apply_mmr_diversity(
    chunks: list[RetrievedChunk],
    top_n: int,
    lambda_param: float = DEFAULT_MMR_LAMBDA
) -> list[RetrievedChunk]:
    """Apply Maximal Marginal Relevance for diverse chunk selection.

    MMR balances relevance and diversity by iteratively selecting chunks
    that maximize: λ * relevance - (1-λ) * max_similarity_to_selected

    Args:
        chunks: Chunks sorted by final_score (descending)
        top_n: Number of chunks to select
        lambda_param: Balance parameter (0.7 = 70% relevance, 30% diversity)

    Returns:
        Selected chunks with diverse content
    """
    if not chunks or len(chunks) <= top_n:
        return chunks

    # Normalize scores to [0, 1] for fair comparison with similarity
    scores = [c.final_score for c in chunks]
    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score if max_score != min_score else 1.0

    def normalized_score(chunk: RetrievedChunk) -> float:
        return (chunk.final_score - min_score) / score_range

    # Start with the highest-scoring chunk
    selected = [chunks[0]]
    remaining = list(chunks[1:])

    while len(selected) < top_n and remaining:
        best_idx = -1
        best_mmr = float('-inf')

        for i, candidate in enumerate(remaining):
            # Relevance component (normalized)
            relevance = normalized_score(candidate)

            # Diversity component: max similarity to any selected chunk
            max_sim = max(
                _compute_chunk_similarity(candidate, s)
                for s in selected
            )

            # MMR score
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim

            if mmr_score > best_mmr:
                best_mmr = mmr_score
                best_idx = i

        if best_idx >= 0:
            selected.append(remaining.pop(best_idx))

    return selected


def retrieve(
    query_id: int,
    dense_limit: int = DEFAULT_DENSE_LIMIT,
    lexical_limit: int = DEFAULT_LEXICAL_LIMIT,
    rrf_k: int = DEFAULT_RRF_K,
    top_k_rrf: int = DEFAULT_TOP_K_RRF,
    top_n_final: int = DEFAULT_TOP_N_FINAL,
    entity_boost: float = DEFAULT_ENTITY_BOOST,
    min_word_count: int = DEFAULT_MIN_WORD_COUNT,
    min_char_count: int = DEFAULT_MIN_CHAR_COUNT,
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
        min_word_count: Minimum words in chunk content (default 50)
        min_char_count: Minimum characters in chunk content (default 250)
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

        # Filter out chunks that don't meet minimum requirements
        filtered_chunks = [
            c for c in chunks_data
            if _meets_minimum_requirements(c.content, min_word_count, min_char_count)
        ]

        if verbose and len(filtered_chunks) < len(chunks_data):
            filtered_count = len(chunks_data) - len(filtered_chunks)
            print(f"  Filtered out {filtered_count} chunks below minimum length requirements")

        # Build maps with embeddings for MMR diversity
        chunks_map = {c.id: c for c in filtered_chunks}
        embeddings_map = {c.id: c.embedding for c in filtered_chunks}

        # Get work data for enrichment
        work_ids = {c.work_id for c in filtered_chunks}
        works = session.query(Work).filter(Work.id.in_(work_ids)).all()
        works_map = {w.id: w for w in works}

        # Build RetrievedChunk objects (with embeddings for MMR)
        retrieved_chunks = []
        for chunk_id in top_ids:
            if chunk_id not in chunks_map:
                continue

            chunk = chunks_map[chunk_id]
            work = works_map.get(chunk.work_id)

            # Enrich content
            enriched = _enrich_content(chunk, work) if work else chunk.content

            # Option B: Keep breadcrumbs separate, reranker sees content only
            # Breadcrumbs are stored in heading_breadcrumbs field and saved context

            # Get embedding as numpy array for MMR (if available)
            embedding = embeddings_map.get(chunk_id)
            np_embedding = None
            if embedding is not None:
                np_embedding = np.array(embedding, dtype=np.float32)

            retrieved_chunks.append(RetrievedChunk(
                id=chunk.id,
                parent_id=chunk.parent_id,
                work_id=chunk.work_id,
                content=chunk.content,
                enriched_content=enriched,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                level=chunk.level,
                heading_breadcrumbs=chunk.heading_breadcrumbs,
                rrf_score=rrf_scores[chunk_id],
                _embedding=np_embedding
            ))

        if verbose:
            print(f"  Reranking {len(retrieved_chunks)} candidates...")

        # BGE reranking
        retrieved_chunks = _rerank_chunks(query.original_query, retrieved_chunks)

        # Apply entity bias
        entities = query.entities or []
        retrieved_chunks = _apply_entity_bias(retrieved_chunks, entities, entity_boost)

        # Apply intent bias
        retrieved_chunks = _apply_intent_bias(retrieved_chunks, query.intent)

        # Sort by final_score before MMR
        retrieved_chunks.sort(key=lambda x: x.final_score, reverse=True)

        # Apply MMR diversity for final selection
        if verbose:
            print(f"  Applying MMR diversity selection...")
        final_chunks = _apply_mmr_diversity(retrieved_chunks, top_n_final)

        if verbose:
            print(f"  Final selection: {len(final_chunks)} chunks (with diversity)")

        # Save to database
        context_data = []
        for chunk in final_chunks:
            context_data.append({
                "id": chunk.id,
                "parent_id": chunk.parent_id,
                "work_id": chunk.work_id,
                "content": chunk.content,
                "heading_breadcrumbs": chunk.heading_breadcrumbs,
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
