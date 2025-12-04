"""
Unit tests for query_embeddings module.

Tests query vectorization, batch processing, pending queries counting,
result dataclasses, and error handling with mocked embedding API calls.
"""

import pytest
from unittest.mock import MagicMock, patch

from psychrag.data.models.query import Query
from psychrag.retrieval.query_embeddings import (
    vectorize_query,
    vectorize_all_queries,
    get_pending_queries_count,
    QueryVectorizationResult,
    BatchVectorizationResult,
)


class TestQueryVectorizationResult:
    """Test QueryVectorizationResult dataclass."""

    def test_query_vectorization_result_success(self):
        """Test QueryVectorizationResult with successful vectorization."""
        result = QueryVectorizationResult(
            query_id=1,
            total_embeddings=3,
            original_count=1,
            mqe_count=1,
            hyde_count=1,
            success=True
        )

        assert result.query_id == 1
        assert result.total_embeddings == 3
        assert result.original_count == 1
        assert result.mqe_count == 1
        assert result.hyde_count == 1
        assert result.success is True
        assert result.error is None

    def test_query_vectorization_result_error(self):
        """Test QueryVectorizationResult with error."""
        result = QueryVectorizationResult(
            query_id=1,
            total_embeddings=0,
            original_count=0,
            mqe_count=0,
            hyde_count=0,
            success=False,
            error="API error"
        )

        assert result.query_id == 1
        assert result.total_embeddings == 0
        assert result.success is False
        assert result.error == "API error"


class TestBatchVectorizationResult:
    """Test BatchVectorizationResult dataclass."""

    def test_batch_vectorization_result_success(self):
        """Test BatchVectorizationResult with successful batch."""
        result = BatchVectorizationResult(
            total_queries=5,
            processed=5,
            success=5,
            failed=0,
            total_embeddings=15,
            errors=[]
        )

        assert result.total_queries == 5
        assert result.processed == 5
        assert result.success == 5
        assert result.failed == 0
        assert result.total_embeddings == 15
        assert result.errors == []

    def test_batch_vectorization_result_with_errors(self):
        """Test BatchVectorizationResult with some failures."""
        errors = [(2, "API timeout"), (4, "Rate limit exceeded")]
        result = BatchVectorizationResult(
            total_queries=5,
            processed=5,
            success=3,
            failed=2,
            total_embeddings=9,
            errors=errors
        )

        assert result.total_queries == 5
        assert result.processed == 5
        assert result.success == 3
        assert result.failed == 2
        assert result.total_embeddings == 9
        assert result.errors == errors
        assert len(result.errors) == 2


class TestGetPendingQueriesCount:
    """Test get_pending_queries_count function."""

    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_get_pending_queries_count_zero(self, mock_get_session, session):
        """Test count when no pending queries exist."""
        mock_get_session.return_value.__enter__.return_value = session

        count = get_pending_queries_count()

        assert count == 0

    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_get_pending_queries_count_single(self, mock_get_session, session):
        """Test count with one pending query."""
        mock_get_session.return_value.__enter__.return_value = session

        query = Query(
            original_query="Test query",
            vector_status="to_vec"
        )
        session.add(query)
        session.commit()

        count = get_pending_queries_count()

        assert count == 1

    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_get_pending_queries_count_multiple(self, mock_get_session, session):
        """Test count with multiple pending queries."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create queries with different statuses
        pending1 = Query(original_query="Query 1", vector_status="to_vec")
        pending2 = Query(original_query="Query 2", vector_status="to_vec")
        processed = Query(original_query="Query 3", vector_status="vec")
        error = Query(original_query="Query 4", vector_status="vec_err")

        session.add_all([pending1, pending2, processed, error])
        session.commit()

        count = get_pending_queries_count()

        assert count == 2


class TestVectorizeQuery:
    """Test vectorize_query function."""

    @patch('psychrag.ai.llm_factory.create_embeddings')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_query_basic(self, mock_get_session, mock_create_embeddings, session):
        """Test vectorizing a query with only original query."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create mock embeddings model
        mock_embeddings_model = MagicMock()
        mock_embeddings_model.embed_documents.return_value = [
            [0.1] * 768  # Mock 768-dim embedding
        ]
        mock_create_embeddings.return_value = mock_embeddings_model

        # Create query
        query = Query(
            original_query="What is psychology?",
            vector_status="to_vec"
        )
        session.add(query)
        session.commit()
        query_id = query.id

        result = vectorize_query(query_id)

        # Verify result
        assert result.success is True
        assert result.query_id == query_id
        assert result.total_embeddings == 1
        assert result.original_count == 1
        assert result.mqe_count == 0
        assert result.hyde_count == 0
        assert result.error is None

        # Verify embeddings were called
        mock_embeddings_model.embed_documents.assert_called_once_with(["What is psychology?"])

        # Verify query was updated
        session.refresh(query)
        assert query.vector_status == "vec"
        assert query.embedding_original is not None
        assert len(query.embedding_original) == 768
        assert query.embedding_original[0] == 0.1  # Check first value
        assert query.embeddings_mqe is None
        assert query.embedding_hyde is None

    @patch('psychrag.ai.llm_factory.create_embeddings')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_query_with_mqe(self, mock_get_session, mock_create_embeddings, session):
        """Test vectorizing a query with MQE expanded queries."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create mock embeddings model
        mock_embeddings_model = MagicMock()
        mock_embeddings_model.embed_documents.return_value = [
            [0.1] * 768,  # Original
            [0.2] * 768,  # MQE 1
            [0.3] * 768,  # MQE 2
        ]
        mock_create_embeddings.return_value = mock_embeddings_model

        # Create query with MQE
        query = Query(
            original_query="What is psychology?",
            expanded_queries=["What is cognitive psychology?", "What is behavioral psychology?"],
            vector_status="to_vec"
        )
        session.add(query)
        session.commit()
        query_id = query.id

        result = vectorize_query(query_id)

        # Verify result
        assert result.success is True
        assert result.total_embeddings == 3
        assert result.original_count == 1
        assert result.mqe_count == 2
        assert result.hyde_count == 0

        # Verify embeddings were called with all texts
        expected_texts = [
            "What is psychology?",
            "What is cognitive psychology?",
            "What is behavioral psychology?"
        ]
        mock_embeddings_model.embed_documents.assert_called_once_with(expected_texts)

        # Verify query was updated
        session.refresh(query)
        assert query.vector_status == "vec"
        assert query.embedding_original is not None
        assert len(query.embedding_original) == 768
        assert query.embedding_original[0] == 0.1  # Check first value
        assert len(query.embeddings_mqe) == 2
        assert len(query.embeddings_mqe[0]) == 768
        assert len(query.embeddings_mqe[1]) == 768
        assert query.embeddings_mqe[0][0] == 0.2  # Check first MQE embedding
        assert query.embeddings_mqe[1][0] == 0.3  # Check second MQE embedding
        assert query.embedding_hyde is None

    @patch('psychrag.ai.llm_factory.create_embeddings')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_query_with_hyde(self, mock_get_session, mock_create_embeddings, session):
        """Test vectorizing a query with HyDE answer."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create mock embeddings model
        mock_embeddings_model = MagicMock()
        mock_embeddings_model.embed_documents.return_value = [
            [0.1] * 768,  # Original
            [0.4] * 768,  # HyDE
        ]
        mock_create_embeddings.return_value = mock_embeddings_model

        # Create query with HyDE
        query = Query(
            original_query="What is psychology?",
            hyde_answer="Psychology is the scientific study of mind and behavior.",
            vector_status="to_vec"
        )
        session.add(query)
        session.commit()
        query_id = query.id

        result = vectorize_query(query_id)

        # Verify result
        assert result.success is True
        assert result.total_embeddings == 2
        assert result.original_count == 1
        assert result.mqe_count == 0
        assert result.hyde_count == 1

        # Verify embeddings were called
        expected_texts = [
            "What is psychology?",
            "Psychology is the scientific study of mind and behavior."
        ]
        mock_embeddings_model.embed_documents.assert_called_once_with(expected_texts)

        # Verify query was updated
        session.refresh(query)
        assert query.vector_status == "vec"
        assert query.embedding_original is not None
        assert len(query.embedding_original) == 768
        assert query.embedding_original[0] == 0.1  # Check first value
        assert query.embedding_hyde is not None
        assert len(query.embedding_hyde) == 768
        assert query.embedding_hyde[0] == 0.4  # Check first value

    @patch('psychrag.ai.llm_factory.create_embeddings')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_query_with_all_fields(self, mock_get_session, mock_create_embeddings, session):
        """Test vectorizing a query with original, MQE, and HyDE."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create mock embeddings model
        mock_embeddings_model = MagicMock()
        mock_embeddings_model.embed_documents.return_value = [
            [0.1] * 768,  # Original
            [0.2] * 768,  # MQE 1
            [0.3] * 768,  # MQE 2
            [0.4] * 768,  # HyDE
        ]
        mock_create_embeddings.return_value = mock_embeddings_model

        # Create query with all fields
        query = Query(
            original_query="What is psychology?",
            expanded_queries=["What is cognitive psychology?", "What is behavioral psychology?"],
            hyde_answer="Psychology is the scientific study of mind and behavior.",
            vector_status="to_vec"
        )
        session.add(query)
        session.commit()
        query_id = query.id

        result = vectorize_query(query_id)

        # Verify result
        assert result.success is True
        assert result.total_embeddings == 4
        assert result.original_count == 1
        assert result.mqe_count == 2
        assert result.hyde_count == 1

        # Verify query was updated correctly
        session.refresh(query)
        assert query.vector_status == "vec"
        assert query.embedding_original is not None
        assert len(query.embedding_original) == 768
        assert query.embedding_original[0] == 0.1  # Check first value
        assert len(query.embeddings_mqe) == 2
        assert len(query.embeddings_mqe[0]) == 768
        assert len(query.embeddings_mqe[1]) == 768
        assert query.embeddings_mqe[0][0] == 0.2  # Check first MQE embedding
        assert query.embeddings_mqe[1][0] == 0.3  # Check second MQE embedding
        assert query.embedding_hyde is not None
        assert len(query.embedding_hyde) == 768
        assert query.embedding_hyde[0] == 0.4  # Check first value

    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_query_not_found(self, mock_get_session, session):
        """Test vectorizing a non-existent query raises ValueError."""
        mock_get_session.return_value.__enter__.return_value = session

        with pytest.raises(ValueError, match="Query with ID 999 not found"):
            vectorize_query(999)

    @patch('psychrag.ai.llm_factory.create_embeddings')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_query_embedding_error(self, mock_get_session, mock_create_embeddings, session):
        """Test vectorization error handling when embedding API fails."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create mock embeddings model that raises an error
        mock_embeddings_model = MagicMock()
        mock_embeddings_model.embed_documents.side_effect = Exception("API rate limit exceeded")
        mock_create_embeddings.return_value = mock_embeddings_model

        # Create query
        query = Query(
            original_query="What is psychology?",
            vector_status="to_vec"
        )
        session.add(query)
        session.commit()
        query_id = query.id

        result = vectorize_query(query_id)

        # Verify result indicates failure
        assert result.success is False
        assert result.query_id == query_id
        assert result.total_embeddings == 0
        assert result.error == "API rate limit exceeded"

        # Verify query status was updated to error
        session.refresh(query)
        assert query.vector_status == "vec_err"

    @patch('psychrag.ai.llm_factory.create_embeddings')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_query_verbose(self, mock_get_session, mock_create_embeddings, session, capsys):
        """Test vectorize_query with verbose output."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create mock embeddings model
        mock_embeddings_model = MagicMock()
        mock_embeddings_model.embed_documents.return_value = [
            [0.1] * 768
        ]
        mock_create_embeddings.return_value = mock_embeddings_model

        # Create query
        query = Query(
            original_query="What is psychology?",
            vector_status="to_vec"
        )
        session.add(query)
        session.commit()
        query_id = query.id

        result = vectorize_query(query_id, verbose=True)

        # Verify verbose output
        captured = capsys.readouterr()
        assert "Vectorizing query" in captured.out
        assert "Generating 1 embeddings" in captured.out
        assert "Successfully vectorized" in captured.out
        assert result.success is True

    @patch('psychrag.ai.llm_factory.create_embeddings')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_query_empty_mqe_list(self, mock_get_session, mock_create_embeddings, session):
        """Test vectorizing a query with empty MQE list."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create mock embeddings model
        mock_embeddings_model = MagicMock()
        mock_embeddings_model.embed_documents.return_value = [
            [0.1] * 768  # Only original
        ]
        mock_create_embeddings.return_value = mock_embeddings_model

        # Create query with empty MQE list
        query = Query(
            original_query="What is psychology?",
            expanded_queries=[],  # Empty list
            vector_status="to_vec"
        )
        session.add(query)
        session.commit()
        query_id = query.id

        result = vectorize_query(query_id)

        # Verify result
        assert result.success is True
        assert result.total_embeddings == 1
        assert result.mqe_count == 0

        # Verify only original was embedded
        mock_embeddings_model.embed_documents.assert_called_once_with(["What is psychology?"])


class TestVectorizeAllQueries:
    """Test vectorize_all_queries function."""

    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_all_queries_empty(self, mock_get_session, session):
        """Test batch vectorization when no pending queries exist."""
        mock_get_session.return_value.__enter__.return_value = session

        result = vectorize_all_queries()

        assert result.total_queries == 0
        assert result.processed == 0
        assert result.success == 0
        assert result.failed == 0
        assert result.total_embeddings == 0
        assert result.errors == []

    @patch('psychrag.retrieval.query_embeddings.vectorize_query')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_all_queries_single_success(self, mock_get_session, mock_vectorize_query, session):
        """Test batch vectorization with one successful query."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create pending query
        query = Query(
            original_query="Test query",
            vector_status="to_vec"
        )
        session.add(query)
        session.commit()

        # Mock successful vectorization
        mock_vectorize_query.return_value = QueryVectorizationResult(
            query_id=query.id,
            total_embeddings=1,
            original_count=1,
            mqe_count=0,
            hyde_count=0,
            success=True
        )

        result = vectorize_all_queries()

        assert result.total_queries == 1
        assert result.processed == 1
        assert result.success == 1
        assert result.failed == 0
        assert result.total_embeddings == 1
        assert result.errors == []
        mock_vectorize_query.assert_called_once_with(query.id, verbose=False)

    @patch('psychrag.retrieval.query_embeddings.vectorize_query')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_all_queries_multiple_success(self, mock_get_session, mock_vectorize_query, session):
        """Test batch vectorization with multiple successful queries."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create multiple pending queries
        queries = [
            Query(original_query=f"Query {i}", vector_status="to_vec")
            for i in range(3)
        ]
        session.add_all(queries)
        session.commit()

        # Mock successful vectorizations
        def mock_vectorize_side_effect(query_id, verbose=False):
            return QueryVectorizationResult(
                query_id=query_id,
                total_embeddings=2,  # Each has 2 embeddings
                original_count=1,
                mqe_count=1,
                hyde_count=0,
                success=True
            )

        mock_vectorize_query.side_effect = mock_vectorize_side_effect

        result = vectorize_all_queries()

        assert result.total_queries == 3
        assert result.processed == 3
        assert result.success == 3
        assert result.failed == 0
        assert result.total_embeddings == 6  # 3 queries * 2 embeddings each
        assert result.errors == []
        assert mock_vectorize_query.call_count == 3

    @patch('psychrag.retrieval.query_embeddings.vectorize_query')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_all_queries_with_failures(self, mock_get_session, mock_vectorize_query, session):
        """Test batch vectorization with some failures."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create multiple pending queries
        queries = [
            Query(original_query=f"Query {i}", vector_status="to_vec")
            for i in range(3)
        ]
        session.add_all(queries)
        session.commit()

        # Mock mixed results: success, failure, success
        def mock_vectorize_side_effect(query_id, verbose=False):
            if query_id == queries[1].id:
                return QueryVectorizationResult(
                    query_id=query_id,
                    total_embeddings=0,
                    original_count=0,
                    mqe_count=0,
                    hyde_count=0,
                    success=False,
                    error="API error"
                )
            else:
                return QueryVectorizationResult(
                    query_id=query_id,
                    total_embeddings=1,
                    original_count=1,
                    mqe_count=0,
                    hyde_count=0,
                    success=True
                )

        mock_vectorize_query.side_effect = mock_vectorize_side_effect

        result = vectorize_all_queries()

        assert result.total_queries == 3
        assert result.processed == 3
        assert result.success == 2
        assert result.failed == 1
        assert result.total_embeddings == 2  # Only successful queries contribute
        assert len(result.errors) == 1
        assert result.errors[0][0] == queries[1].id
        assert result.errors[0][1] == "API error"

    @patch('psychrag.retrieval.query_embeddings.vectorize_query')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_all_queries_all_failures(self, mock_get_session, mock_vectorize_query, session):
        """Test batch vectorization when all queries fail."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create pending queries
        queries = [
            Query(original_query=f"Query {i}", vector_status="to_vec")
            for i in range(2)
        ]
        session.add_all(queries)
        session.commit()

        # Mock all failures
        mock_vectorize_query.return_value = QueryVectorizationResult(
            query_id=queries[0].id,
            total_embeddings=0,
            original_count=0,
            mqe_count=0,
            hyde_count=0,
            success=False,
            error="Network timeout"
        )

        result = vectorize_all_queries()

        assert result.total_queries == 2
        assert result.processed == 2
        assert result.success == 0
        assert result.failed == 2
        assert result.total_embeddings == 0
        assert len(result.errors) == 2

    @patch('psychrag.retrieval.query_embeddings.vectorize_query')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_all_queries_verbose(self, mock_get_session, mock_vectorize_query, session, capsys):
        """Test batch vectorization with verbose output."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create pending queries
        queries = [
            Query(original_query=f"Query {i}", vector_status="to_vec")
            for i in range(2)
        ]
        session.add_all(queries)
        session.commit()

        # Mock successful vectorizations
        mock_vectorize_query.return_value = QueryVectorizationResult(
            query_id=queries[0].id,
            total_embeddings=1,
            original_count=1,
            mqe_count=0,
            hyde_count=0,
            success=True
        )

        result = vectorize_all_queries(verbose=True)

        # Verify verbose output
        captured = capsys.readouterr()
        assert "Found 2 queries to vectorize" in captured.out
        assert "Processing query" in captured.out
        assert "Completed:" in captured.out
        assert result.total_queries == 2

    @patch('psychrag.retrieval.query_embeddings.vectorize_query')
    @patch('psychrag.retrieval.query_embeddings.get_session')
    def test_vectorize_all_queries_mixed_embeddings(self, mock_get_session, mock_vectorize_query, session):
        """Test batch vectorization with queries having different embedding counts."""
        mock_get_session.return_value.__enter__.return_value = session

        # Create pending queries
        queries = [
            Query(original_query=f"Query {i}", vector_status="to_vec")
            for i in range(3)
        ]
        session.add_all(queries)
        session.commit()

        # Mock different embedding counts
        embedding_counts = [1, 3, 2]  # Original only, Original+MQE+HyDE, Original+MQE

        def mock_vectorize_side_effect(query_id, verbose=False):
            idx = next(i for i, q in enumerate(queries) if q.id == query_id)
            return QueryVectorizationResult(
                query_id=query_id,
                total_embeddings=embedding_counts[idx],
                original_count=1,
                mqe_count=embedding_counts[idx] - 1,
                hyde_count=0,
                success=True
            )

        mock_vectorize_query.side_effect = mock_vectorize_side_effect

        result = vectorize_all_queries()

        assert result.total_queries == 3
        assert result.success == 3
        assert result.total_embeddings == 6  # 1 + 3 + 2 = 6

