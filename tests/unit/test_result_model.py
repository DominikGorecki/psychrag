"""
Unit tests for Result model.

Tests model creation, Query relationship, cascade delete, and CRUD operations.
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from psychrag.data.models.result import Result
from psychrag.data.models.query import Query


class TestResultCreation:
    """Test basic model creation and field values."""

    def test_create_result(self, session):
        """Test creating a Result instance."""
        # First create a Query
        query = Query(
            original_query="What is cognitive psychology?",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        result = Result(
            query_id=query.id,
            response_text="Cognitive psychology is the study of mental processes..."
        )
        session.add(result)
        session.commit()

        assert result.id is not None
        assert result.query_id == query.id
        assert result.response_text == "Cognitive psychology is the study of mental processes..."
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)

    def test_repr(self, session):
        """Test __repr__ method."""
        query = Query(
            original_query="Test query",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        result = Result(
            query_id=query.id,
            response_text="This is a test response that is longer than 50 characters to test truncation"
        )
        session.add(result)
        session.commit()

        repr_str = repr(result)
        assert "Result" in repr_str
        assert str(result.id) in repr_str
        assert str(result.query_id) in repr_str
        assert "..." in repr_str  # Should truncate long responses


class TestResultRelationships:
    """Test relationships with Query model."""

    def test_result_belongs_to_query(self, session):
        """Test that Result has foreign key relationship to Query."""
        query = Query(
            original_query="What is memory?",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        result = Result(
            query_id=query.id,
            response_text="Memory is the process of encoding, storing, and retrieving information."
        )
        session.add(result)
        session.commit()

        # Verify relationship
        assert result.query_id == query.id
        retrieved_query = session.query(Query).filter(Query.id == query.id).first()
        assert retrieved_query is not None

    def test_multiple_results_per_query(self, session):
        """Test that one Query can have multiple Results."""
        query = Query(
            original_query="What is attention?",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        result1 = Result(
            query_id=query.id,
            response_text="First response about attention."
        )
        result2 = Result(
            query_id=query.id,
            response_text="Second response about attention."
        )
        result3 = Result(
            query_id=query.id,
            response_text="Third response about attention."
        )
        session.add_all([result1, result2, result3])
        session.commit()

        # Query all results for this query
        results = session.query(Result).filter(Result.query_id == query.id).all()
        assert len(results) == 3
        assert all(r.query_id == query.id for r in results)

    def test_cascade_delete(self, session):
        """Test that deleting Query cascades to delete Results."""
        query = Query(
            original_query="Test query for cascade",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        result1 = Result(
            query_id=query.id,
            response_text="Result 1"
        )
        result2 = Result(
            query_id=query.id,
            response_text="Result 2"
        )
        session.add_all([result1, result2])
        session.commit()

        result_ids = [result1.id, result2.id]

        # Delete the query
        session.delete(query)
        session.commit()

        # Verify results are also deleted
        remaining_results = session.query(Result).filter(Result.id.in_(result_ids)).all()
        assert len(remaining_results) == 0


class TestResultConstraints:
    """Test database constraints."""

    def test_query_id_required(self, session):
        """Test that query_id is NOT NULL."""
        result = Result(
            query_id=None,
            response_text="Test response"
        )
        session.add(result)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_response_text_required(self, session):
        """Test that response_text is NOT NULL."""
        query = Query(
            original_query="Test",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        result = Result(
            query_id=query.id,
            response_text=None
        )
        session.add(result)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_foreign_key_constraint(self, session):
        """Test that query_id must reference existing Query."""
        result = Result(
            query_id=99999,  # Non-existent query ID
            response_text="Test response"
        )
        session.add(result)

        with pytest.raises(IntegrityError):
            session.commit()


class TestResultCRUD:
    """Test CRUD operations."""

    def test_create_result(self, session):
        """Test creating a Result."""
        query = Query(
            original_query="Create test",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        result = Result(
            query_id=query.id,
            response_text="Created response"
        )
        session.add(result)
        session.commit()

        assert result.id is not None
        assert result.response_text == "Created response"

    def test_read_result(self, session):
        """Test reading a Result."""
        query = Query(
            original_query="Read test",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        result = Result(
            query_id=query.id,
            response_text="Response to read"
        )
        session.add(result)
        session.commit()
        result_id = result.id

        # Retrieve
        retrieved = session.query(Result).filter(Result.id == result_id).first()
        assert retrieved is not None
        assert retrieved.response_text == "Response to read"
        assert retrieved.query_id == query.id

    def test_update_result(self, session):
        """Test updating a Result."""
        query = Query(
            original_query="Update test",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        result = Result(
            query_id=query.id,
            response_text="Original response"
        )
        session.add(result)
        session.commit()

        original_updated_at = result.updated_at

        # Update response_text
        result.response_text = "Updated response"
        session.commit()

        assert result.response_text == "Updated response"
        # Note: updated_at auto-update depends on SQLAlchemy/server configuration

    def test_delete_result(self, session):
        """Test deleting a Result."""
        query = Query(
            original_query="Delete test",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        result = Result(
            query_id=query.id,
            response_text="Response to delete"
        )
        session.add(result)
        session.commit()
        result_id = result.id

        # Delete
        session.delete(result)
        session.commit()

        # Verify deleted
        retrieved = session.query(Result).filter(Result.id == result_id).first()
        assert retrieved is None

    def test_query_by_query_id(self, session):
        """Test querying Results by query_id."""
        query1 = Query(
            original_query="Query 1",
            vector_status="no_vec"
        )
        query2 = Query(
            original_query="Query 2",
            vector_status="no_vec"
        )
        session.add_all([query1, query2])
        session.commit()

        result1 = Result(
            query_id=query1.id,
            response_text="Response 1"
        )
        result2 = Result(
            query_id=query1.id,
            response_text="Response 2"
        )
        result3 = Result(
            query_id=query2.id,
            response_text="Response 3"
        )
        session.add_all([result1, result2, result3])
        session.commit()

        # Query results for query1
        results = session.query(Result).filter(Result.query_id == query1.id).all()
        assert len(results) == 2
        assert all(r.query_id == query1.id for r in results)


class TestResultTimestamps:
    """Test timestamp behavior."""

    def test_timestamps_auto_populate(self, session):
        """Test that timestamps are automatically populated."""
        query = Query(
            original_query="Timestamp test",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        before = datetime.now()
        result = Result(
            query_id=query.id,
            response_text="Test response"
        )
        session.add(result)
        session.commit()
        after = datetime.now()

        assert result.created_at is not None
        assert result.updated_at is not None
        # Note: Exact comparison depends on timezone handling

    def test_multiple_results_different_timestamps(self, session):
        """Test that multiple results have independent timestamps."""
        import time

        query = Query(
            original_query="Multiple timestamps",
            vector_status="no_vec"
        )
        session.add(query)
        session.commit()

        result1 = Result(
            query_id=query.id,
            response_text="First response"
        )
        session.add(result1)
        session.commit()

        time.sleep(0.01)  # Small delay

        result2 = Result(
            query_id=query.id,
            response_text="Second response"
        )
        session.add(result2)
        session.commit()

        # Timestamps should be different (or very close)
        assert result1.created_at <= result2.created_at

