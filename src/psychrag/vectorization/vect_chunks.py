"""Vectorize chunks using embedding models.

This module creates vector embeddings for chunks in the database
that are marked for vectorization (vector_status='to_vec').

Usage:
    from psychrag.vectorization.vect_chunks import vectorize_chunks
    result = vectorize_chunks(work_id=1, limit=10, verbose=True)

Examples:
    # Vectorize up to 10 chunks for work ID 1
    from psychrag.vectorization.vect_chunks import vectorize_chunks
    result = vectorize_chunks(1, limit=10)
    print(f"Vectorized {result['success']} chunks")
"""

from dataclasses import dataclass

from psychrag.ai.llm_factory import create_embeddings
from psychrag.data.database import get_session
from psychrag.data.models import Chunk, Work


@dataclass
class VectorizationResult:
    """Result of vectorization operation."""

    total_eligible: int
    processed: int
    success: int
    failed: int
    errors: list[tuple[int, str]]  # (chunk_id, error_message)


def get_eligible_chunks_count(work_id: int) -> int:
    """Get count of chunks eligible for vectorization.

    Args:
        work_id: ID of the work in the database.

    Returns:
        Number of eligible chunks.
    """
    with get_session() as session:
        return session.query(Chunk).filter(
            Chunk.work_id == work_id,
            Chunk.vector_status == 'to_vec',
            Chunk.parent_id.isnot(None),
            Chunk.embedding.is_(None)
        ).count()


def vectorize_chunks(
    work_id: int,
    limit: int | None = None,
    batch_size: int = 20,
    verbose: bool = False
) -> VectorizationResult:
    """Vectorize chunks for a work using embedding model.

    Args:
        work_id: ID of the work in the database.
        limit: Maximum number of chunks to process (None for all).
        batch_size: Number of chunks to embed in a single API call.
        verbose: Whether to print progress information.

    Returns:
        VectorizationResult with counts and any errors.

    Raises:
        ValueError: If work not found.
    """
    with get_session() as session:
        # Verify work exists
        work = session.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"Work with ID {work_id} not found")

        if verbose:
            print(f"Processing work {work_id}: {work.title}")

        # Get eligible chunks
        query = session.query(Chunk).filter(
            Chunk.work_id == work_id,
            Chunk.vector_status == 'to_vec',
            Chunk.parent_id.isnot(None),
            Chunk.embedding.is_(None)
        ).order_by(Chunk.id)

        total_eligible = query.count()

        if limit:
            chunks = query.limit(limit).all()
        else:
            chunks = query.all()

        if verbose:
            print(f"Found {total_eligible} eligible chunks, processing {len(chunks)}")

        if not chunks:
            return VectorizationResult(
                total_eligible=total_eligible,
                processed=0,
                success=0,
                failed=0,
                errors=[]
            )

        # Create embeddings model
        embeddings_model = create_embeddings()

        success_count = 0
        failed_count = 0
        errors = []

        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_texts = [chunk.content for chunk in batch]

            if verbose:
                print(f"  Processing batch {i // batch_size + 1} ({len(batch)} chunks)...")

            try:
                # Get embeddings for batch
                embeddings = embeddings_model.embed_documents(batch_texts)

                # Update each chunk
                for chunk, embedding in zip(batch, embeddings):
                    try:
                        chunk.embedding = embedding
                        chunk.vector_status = 'vec'
                        success_count += 1
                    except Exception as e:
                        chunk.vector_status = 'vec_err'
                        failed_count += 1
                        errors.append((chunk.id, str(e)))
                        if verbose:
                            print(f"    Error updating chunk {chunk.id}: {e}")

            except Exception as e:
                # Batch failed - mark all chunks in batch as error
                for chunk in batch:
                    chunk.vector_status = 'vec_err'
                    failed_count += 1
                    errors.append((chunk.id, str(e)))

                if verbose:
                    print(f"    Batch error: {e}")

            # Commit after each batch
            session.commit()

        if verbose:
            print(f"\nCompleted: {success_count} success, {failed_count} failed")

        return VectorizationResult(
            total_eligible=total_eligible,
            processed=len(chunks),
            success=success_count,
            failed=failed_count,
            errors=errors
        )
