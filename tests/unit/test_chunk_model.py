"""
Unit tests for Chunk model.

Tests model creation, relationships (parent, work, children), vector embedding field,
validation logic, and CRUD operations.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from psychrag.data.models.chunk import Chunk
from psychrag.data.models.work import Work


class TestChunkCreation:
    """Test basic model creation and field values."""

    def test_create_chunk_basic(self, session):
        """Test creating a Chunk with basic fields."""
        # Create a Work first
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level="H1",
            content="Chapter 1 content",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)
        session.commit()

        assert chunk.id is not None
        assert chunk.work_id == work.id
        assert chunk.level == "H1"
        assert chunk.content == "Chapter 1 content"
        assert chunk.start_line == 1
        assert chunk.end_line == 10
        assert chunk.vector_status == "no_vec"
        assert chunk.parent_id is None
        assert chunk.embedding is None
        assert chunk.heading_breadcrumbs is None

    def test_create_chunk_with_parent(self, session):
        """Test creating a Chunk with parent relationship."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        parent_chunk = Chunk(
            work_id=work.id,
            level="H1",
            content="Parent content",
            start_line=1,
            end_line=20,
            vector_status="no_vec"
        )
        session.add(parent_chunk)
        session.commit()

        child_chunk = Chunk(
            work_id=work.id,
            parent_id=parent_chunk.id,
            level="H2",
            content="Child content",
            start_line=21,
            end_line=30,
            vector_status="no_vec"
        )
        session.add(child_chunk)
        session.commit()

        assert child_chunk.parent_id == parent_chunk.id
        assert child_chunk.level == "H2"

    def test_create_chunk_with_breadcrumbs(self, session):
        """Test creating a Chunk with heading breadcrumbs."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level="H3",
            content="Subsection content",
            heading_breadcrumbs="H1 > H2 > H3",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)
        session.commit()

        assert chunk.heading_breadcrumbs == "H1 > H2 > H3"

    def test_repr(self, session):
        """Test __repr__ method."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level="H1",
            content="Test content",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)
        session.commit()

        repr_str = repr(chunk)
        assert "Chunk" in repr_str
        assert str(chunk.id) in repr_str
        assert "H1" in repr_str
        assert str(work.id) in repr_str


class TestChunkRelationships:
    """Test relationships (parent, work, children)."""

    def test_chunk_belongs_to_work(self, session):
        """Test that Chunk has foreign key relationship to Work."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level="H1",
            content="Content",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)
        session.commit()

        assert chunk.work_id == work.id
        retrieved_work = session.query(Work).filter(Work.id == work.id).first()
        assert retrieved_work is not None

    def test_parent_child_relationship(self, session):
        """Test parent-child self-referential relationship."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        parent = Chunk(
            work_id=work.id,
            level="H1",
            content="Parent",
            start_line=1,
            end_line=20,
            vector_status="no_vec"
        )
        session.add(parent)
        session.commit()

        child1 = Chunk(
            work_id=work.id,
            parent_id=parent.id,
            level="H2",
            content="Child 1",
            start_line=21,
            end_line=30,
            vector_status="no_vec"
        )
        child2 = Chunk(
            work_id=work.id,
            parent_id=parent.id,
            level="H2",
            content="Child 2",
            start_line=31,
            end_line=40,
            vector_status="no_vec"
        )
        session.add_all([child1, child2])
        session.commit()

        # Test parent relationship
        assert child1.parent_id == parent.id
        assert child2.parent_id == parent.id

        # Test children backref (if available)
        # Note: backref="children" is defined in Chunk model
        session.refresh(parent)
        # Access children through relationship
        children = session.query(Chunk).filter(Chunk.parent_id == parent.id).all()
        assert len(children) == 2

    def test_cascade_delete_from_work(self, session):
        """Test that deleting Work cascades to delete Chunks."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk1 = Chunk(
            work_id=work.id,
            level="H1",
            content="Chunk 1",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        chunk2 = Chunk(
            work_id=work.id,
            level="H2",
            content="Chunk 2",
            start_line=11,
            end_line=20,
            vector_status="no_vec"
        )
        session.add_all([chunk1, chunk2])
        session.commit()

        chunk_ids = [chunk1.id, chunk2.id]
        
        # Expunge chunks from session to prevent SQLAlchemy from trying to update them
        session.expunge(chunk1)
        session.expunge(chunk2)

        # Delete the work - database will cascade delete chunks
        session.delete(work)
        session.commit()

        # Verify chunks are also deleted
        remaining_chunks = session.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
        assert len(remaining_chunks) == 0

    def test_cascade_delete_from_parent(self, session):
        """Test that deleting parent Chunk cascades to delete children."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        parent = Chunk(
            work_id=work.id,
            level="H1",
            content="Parent",
            start_line=1,
            end_line=20,
            vector_status="no_vec"
        )
        session.add(parent)
        session.commit()

        child = Chunk(
            work_id=work.id,
            parent_id=parent.id,
            level="H2",
            content="Child",
            start_line=21,
            end_line=30,
            vector_status="no_vec"
        )
        session.add(child)
        session.commit()
        child_id = child.id
        parent_id = parent.id
        
        # Expunge both parent and child from session to prevent SQLAlchemy 
        # from trying to manage the relationship
        session.expunge(child)
        session.expunge(parent)

        # Delete parent using raw SQL to bypass SQLAlchemy's ORM relationship management
        # This ensures the database-level CASCADE delete happens without ORM interference
        from sqlalchemy import text
        session.execute(text("DELETE FROM chunks WHERE id = :parent_id"), {"parent_id": parent_id})
        session.commit()

        # Verify child is also deleted
        remaining_child = session.query(Chunk).filter(Chunk.id == child_id).first()
        assert remaining_child is None


class TestChunkVectorField:
    """Test vector embedding field handling."""

    def test_chunk_embedding_nullable(self, session):
        """Test that embedding field can be None."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level="H1",
            content="Content",
            start_line=1,
            end_line=10,
            vector_status="no_vec",
            embedding=None
        )
        session.add(chunk)
        session.commit()

        assert chunk.embedding is None

    def test_chunk_vector_status_values(self, session):
        """Test different vector_status values."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        statuses = ["no_vec", "to_vec", "vec", "vec_err"]
        chunks = []

        for status in statuses:
            chunk = Chunk(
                work_id=work.id,
                level="H1",
                content=f"Content {status}",
                start_line=1,
                end_line=10,
                vector_status=status
            )
            chunks.append(chunk)

        session.add_all(chunks)
        session.commit()

        for i, status in enumerate(statuses):
            assert chunks[i].vector_status == status


class TestChunkValidation:
    """Test validation logic and constraints."""

    def test_work_id_required(self, session):
        """Test that work_id is NOT NULL."""
        chunk = Chunk(
            work_id=None,
            level="H1",
            content="Content",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_level_required(self, session):
        """Test that level is NOT NULL."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level=None,
            content="Content",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_content_required(self, session):
        """Test that content is NOT NULL."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level="H1",
            content=None,
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_start_line_required(self, session):
        """Test that start_line is NOT NULL."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level="H1",
            content="Content",
            start_line=None,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_end_line_required(self, session):
        """Test that end_line is NOT NULL."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level="H1",
            content="Content",
            start_line=1,
            end_line=None,
            vector_status="no_vec"
        )
        session.add(chunk)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_vector_status_required(self, session):
        """Test that vector_status is NOT NULL."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        # Create chunk without vector_status to test NOT NULL constraint
        # We need to bypass SQLAlchemy's Python-level default by using insert directly
        from sqlalchemy import insert
        stmt = insert(Chunk.__table__).values(
            work_id=work.id,
            level="H1",
            content="Content",
            start_line=1,
            end_line=10,
            vector_status=None  # Explicitly set to None to test NOT NULL constraint
        )
        
        with pytest.raises(IntegrityError):
            session.execute(stmt)
            session.commit()

    def test_foreign_key_constraint_work(self, session):
        """Test that work_id must reference existing Work."""
        chunk = Chunk(
            work_id=99999,  # Non-existent work ID
            level="H1",
            content="Content",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_foreign_key_constraint_parent(self, session):
        """Test that parent_id must reference existing Chunk."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            parent_id=99999,  # Non-existent parent ID
            level="H2",
            content="Content",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)

        with pytest.raises(IntegrityError):
            session.commit()


class TestChunkCRUD:
    """Test CRUD operations."""

    def test_create_chunk(self, session):
        """Test creating a Chunk."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level="H1",
            content="Created chunk",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)
        session.commit()

        assert chunk.id is not None
        assert chunk.content == "Created chunk"

    def test_read_chunk(self, session):
        """Test reading a Chunk."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level="H1",
            content="Chunk to read",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)
        session.commit()
        chunk_id = chunk.id

        # Retrieve
        retrieved = session.query(Chunk).filter(Chunk.id == chunk_id).first()
        assert retrieved is not None
        assert retrieved.content == "Chunk to read"
        assert retrieved.level == "H1"

    def test_update_chunk(self, session):
        """Test updating a Chunk."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level="H1",
            content="Original content",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)
        session.commit()

        # Update content and vector_status
        chunk.content = "Updated content"
        chunk.vector_status = "vec"
        chunk.heading_breadcrumbs = "H1 > H2"
        session.commit()

        assert chunk.content == "Updated content"
        assert chunk.vector_status == "vec"
        assert chunk.heading_breadcrumbs == "H1 > H2"

    def test_delete_chunk(self, session):
        """Test deleting a Chunk."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk = Chunk(
            work_id=work.id,
            level="H1",
            content="Chunk to delete",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add(chunk)
        session.commit()
        chunk_id = chunk.id

        # Delete
        session.delete(chunk)
        session.commit()

        # Verify deleted
        retrieved = session.query(Chunk).filter(Chunk.id == chunk_id).first()
        assert retrieved is None

    def test_query_by_work_id(self, session):
        """Test querying Chunks by work_id."""
        work1 = Work(
            title="Work 1",
            authors="Author 1"
        )
        work2 = Work(
            title="Work 2",
            authors="Author 2"
        )
        session.add_all([work1, work2])
        session.commit()

        chunk1 = Chunk(
            work_id=work1.id,
            level="H1",
            content="Chunk 1",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        chunk2 = Chunk(
            work_id=work1.id,
            level="H2",
            content="Chunk 2",
            start_line=11,
            end_line=20,
            vector_status="no_vec"
        )
        chunk3 = Chunk(
            work_id=work2.id,
            level="H1",
            content="Chunk 3",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        session.add_all([chunk1, chunk2, chunk3])
        session.commit()

        # Query chunks for work1
        chunks = session.query(Chunk).filter(Chunk.work_id == work1.id).all()
        assert len(chunks) == 2
        assert all(c.work_id == work1.id for c in chunks)

    def test_query_by_level(self, session):
        """Test querying Chunks by level."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk1 = Chunk(
            work_id=work.id,
            level="H1",
            content="H1 chunk",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        chunk2 = Chunk(
            work_id=work.id,
            level="H2",
            content="H2 chunk",
            start_line=11,
            end_line=20,
            vector_status="no_vec"
        )
        chunk3 = Chunk(
            work_id=work.id,
            level="H1",
            content="Another H1 chunk",
            start_line=21,
            end_line=30,
            vector_status="no_vec"
        )
        session.add_all([chunk1, chunk2, chunk3])
        session.commit()

        # Query H1 chunks
        h1_chunks = session.query(Chunk).filter(Chunk.level == "H1").all()
        assert len(h1_chunks) == 2
        assert all(c.level == "H1" for c in h1_chunks)

    def test_query_by_vector_status(self, session):
        """Test querying Chunks by vector_status."""
        work = Work(
            title="Test Work",
            authors="Test Author"
        )
        session.add(work)
        session.commit()

        chunk1 = Chunk(
            work_id=work.id,
            level="H1",
            content="No vec chunk",
            start_line=1,
            end_line=10,
            vector_status="no_vec"
        )
        chunk2 = Chunk(
            work_id=work.id,
            level="H2",
            content="Vec chunk",
            start_line=11,
            end_line=20,
            vector_status="vec"
        )
        session.add_all([chunk1, chunk2])
        session.commit()

        # Query chunks with vector_status="vec"
        vec_chunks = session.query(Chunk).filter(Chunk.vector_status == "vec").all()
        assert len(vec_chunks) == 1
        assert vec_chunks[0].vector_status == "vec"

