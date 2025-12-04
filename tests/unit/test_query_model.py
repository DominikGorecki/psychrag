"""
Unit tests for Query model.

Tests model creation, vector embeddings, JSON fields, CRUD operations, and validation.
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from psychrag.data.models.query import Query


class TestQueryCreation:
    """Test basic model creation and field values."""

    def test_create_query_basic(self, session):
        """Test creating a Query with basic fields."""
        query = Query(
            original_query="What is cognitive psychology?",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        assert query.id is not None
        assert query.original_query == "What is cognitive psychology?"
        assert query.vector_status == "no_vec"
        assert query.expanded_queries is None
        assert query.hyde_answer is None
        assert query.intent is None
        assert query.entities is None
        assert query.embedding_original is None
        assert query.embeddings_mqe is None
        assert query.embedding_hyde is None
        assert query.retrieved_context is None
        assert query.clean_retrieval_context is None
        assert isinstance(query.created_at, datetime)
        assert isinstance(query.updated_at, datetime)

    def test_create_query_with_all_fields(self, session):
        """Test creating a Query with all optional fields."""
        query = Query(
            original_query="What is memory?",
            expanded_queries=["What is memory?", "How does memory work?", "Memory processes"],
            hyde_answer="Memory is the process of encoding, storing, and retrieving information.",
            intent="DEFINITION",
            entities=["memory", "encoding", "retrieval"],
            vector_status="vec",
            retrieved_context=[{"chunk_id": 1, "score": 0.95}],
            clean_retrieval_context=[{"chunk_id": 1, "content": "Memory content"}]
        )
        session.add(query)
        session.commit()

        assert query.expanded_queries == ["What is memory?", "How does memory work?", "Memory processes"]
        assert query.hyde_answer == "Memory is the process of encoding, storing, and retrieving information."
        assert query.intent == "DEFINITION"
        assert query.entities == ["memory", "encoding", "retrieval"]
        assert query.retrieved_context == [{"chunk_id": 1, "score": 0.95}]
        assert query.clean_retrieval_context == [{"chunk_id": 1, "content": "Memory content"}]

    def test_repr(self, session):
        """Test __repr__ method."""
        query = Query(
            original_query="This is a very long query that exceeds fifty characters to test truncation",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        repr_str = repr(query)
        assert "Query" in repr_str
        assert str(query.id) in repr_str
        assert "..." in repr_str  # Should truncate long queries

    def test_repr_short_query(self, session):
        """Test __repr__ with short query (no truncation)."""
        query = Query(
            original_query="Short query",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        repr_str = repr(query)
        assert "Short query" in repr_str
        assert "..." not in repr_str


class TestQueryVectorFields:
    """Test vector embedding fields."""

    def test_embedding_fields_nullable(self, session):
        """Test that embedding fields can be None."""
        query = Query(
            original_query="Test query",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        assert query.embedding_original is None
        assert query.embedding_hyde is None
        assert query.embeddings_mqe is None

    def test_vector_status_values(self, session):
        """Test different vector_status values."""
        statuses = ["no_vec", "to_vec", "vec", "vec_err"]
        queries = []

        for status in statuses:
            query = Query(
                original_query=f"Query with status {status}",
                vector_status=status
            )
            queries.append(query)

        session.add_all(queries)
        session.commit()

        for i, status in enumerate(statuses):
            assert queries[i].vector_status == status


class TestQueryJSONFields:
    """Test JSON field handling."""

    def test_expanded_queries_json(self, session):
        """Test expanded_queries JSON field."""
        query = Query(
            original_query="Test",
            expanded_queries=["Query 1", "Query 2", "Query 3"],
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        assert query.expanded_queries == ["Query 1", "Query 2", "Query 3"]
        assert isinstance(query.expanded_queries, list)

    def test_entities_json(self, session):
        """Test entities JSON field."""
        query = Query(
            original_query="Test",
            entities=["entity1", "entity2", {"name": "entity3", "type": "theory"}],
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        assert len(query.entities) == 3
        assert "entity1" in query.entities
        assert isinstance(query.entities[2], dict)

    def test_retrieved_context_json(self, session):
        """Test retrieved_context JSON field."""
        query = Query(
            original_query="Test",
            retrieved_context=[
                {"chunk_id": 1, "score": 0.95, "content": "Chunk 1"},
                {"chunk_id": 2, "score": 0.87, "content": "Chunk 2"}
            ],
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        assert len(query.retrieved_context) == 2
        assert query.retrieved_context[0]["chunk_id"] == 1
        assert query.retrieved_context[0]["score"] == 0.95

    def test_clean_retrieval_context_json(self, session):
        """Test clean_retrieval_context JSON field."""
        query = Query(
            original_query="Test",
            clean_retrieval_context=[
                {"chunk_id": 1, "content": "Consolidated chunk 1"},
                {"chunk_id": 2, "content": "Consolidated chunk 2"}
            ],
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        assert len(query.clean_retrieval_context) == 2
        assert query.clean_retrieval_context[0]["content"] == "Consolidated chunk 1"

    def test_embeddings_mqe_json(self, session):
        """Test embeddings_mqe JSON field (array of embeddings)."""
        query = Query(
            original_query="Test",
            embeddings_mqe=[
                [0.1, 0.2, 0.3] * 256,  # Mock 768-dim embedding
                [0.4, 0.5, 0.6] * 256,
            ],
            vector_status="vec"
        )
        session.add(query)
        session.commit()

        assert len(query.embeddings_mqe) == 2
        assert isinstance(query.embeddings_mqe, list)


class TestQueryValidation:
    """Test validation logic and constraints."""

    def test_original_query_required(self, session):
        """Test that original_query is NOT NULL."""
        query = Query(
            original_query=None,
            vector_status="no_vec"
        )
        session.add(query)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_vector_status_required(self, session):
        """Test that vector_status is NOT NULL."""
        # We need to bypass SQLAlchemy's Python-level default by using insert directly
        # SQLAlchemy applies defaults at the ORM level, so we use insert() to test DB constraint
        from sqlalchemy import insert
        stmt = insert(Query.__table__).values(
            original_query="Test query",
            vector_status=None  # Explicitly set to None to test NOT NULL constraint
        )
        
        with pytest.raises(IntegrityError):
            session.execute(stmt)
            session.commit()

    def test_vector_status_default(self, session):
        """Test that vector_status defaults to 'no_vec'."""
        query = Query(
            original_query="Test query"
            # vector_status not specified
        )
        session.add(query)
        session.commit()

        assert query.vector_status == "no_vec"


class TestQueryCRUD:
    """Test CRUD operations."""

    def test_create_query(self, session):
        """Test creating a Query."""
        query = Query(
            original_query="Create test query",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        assert query.id is not None
        assert query.original_query == "Create test query"

    def test_read_query(self, session):
        """Test reading a Query."""
        query = Query(
            original_query="Read test query",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()
        query_id = query.id

        # Retrieve
        retrieved = session.query(Query).filter(Query.id == query_id).first()
        assert retrieved is not None
        assert retrieved.original_query == "Read test query"

    def test_update_query(self, session):
        """Test updating a Query."""
        query = Query(
            original_query="Original query",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        # Update fields
        query.original_query = "Updated query"
        query.intent = "MECHANISM"
        query.hyde_answer = "Updated HyDE answer"
        query.vector_status = "vec"
        session.commit()

        assert query.original_query == "Updated query"
        assert query.intent == "MECHANISM"
        assert query.hyde_answer == "Updated HyDE answer"
        assert query.vector_status == "vec"

    def test_delete_query(self, session):
        """Test deleting a Query."""
        query = Query(
            original_query="Query to delete",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()
        query_id = query.id

        # Delete
        session.delete(query)
        session.commit()

        # Verify deleted
        retrieved = session.query(Query).filter(Query.id == query_id).first()
        assert retrieved is None

    def test_query_by_intent(self, session):
        """Test querying Queries by intent."""
        query1 = Query(
            original_query="What is X?",
            intent="DEFINITION",
            vector_status="no_vec"
        )
        query2 = Query(
            original_query="How does X work?",
            intent="MECHANISM",
            vector_status="no_vec"
        )
        query3 = Query(
            original_query="Compare X and Y",
            intent="COMPARISON",
            vector_status="no_vec"
        )
        session.add_all([query1, query2, query3])
        session.commit()

        # Query by intent
        definition_queries = session.query(Query).filter(Query.intent == "DEFINITION").all()
        assert len(definition_queries) == 1
        assert definition_queries[0].intent == "DEFINITION"

    def test_query_by_vector_status(self, session):
        """Test querying Queries by vector_status."""
        query1 = Query(
            original_query="Query 1",
            vector_status="no_vec"
        )
        query2 = Query(
            original_query="Query 2",
            vector_status="vec"
        )
        query3 = Query(
            original_query="Query 3",
            vector_status="to_vec"
        )
        session.add_all([query1, query2, query3])
        session.commit()

        # Query by vector_status
        vec_queries = session.query(Query).filter(Query.vector_status == "vec").all()
        assert len(vec_queries) == 1
        assert vec_queries[0].vector_status == "vec"


class TestQueryTimestamps:
    """Test timestamp behavior."""

    def test_timestamps_auto_populate(self, session):
        """Test that timestamps are automatically populated."""
        before = datetime.now()
        query = Query(
            original_query="Timestamp test",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()
        after = datetime.now()

        assert query.created_at is not None
        assert query.updated_at is not None
        # Note: Exact comparison depends on timezone handling

    def test_multiple_queries_different_timestamps(self, session):
        """Test that multiple queries have independent timestamps."""
        import time

        query1 = Query(
            original_query="Query 1",
            vector_status="no_vec"
        )
        session.add(query1)
        session.commit()

        time.sleep(0.01)  # Small delay

        query2 = Query(
            original_query="Query 2",
            vector_status="no_vec"
        )
        session.add(query2)
        session.commit()

        # Timestamps should be different (or very close)
        assert query1.created_at <= query2.created_at

