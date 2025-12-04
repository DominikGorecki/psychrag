"""
Unit tests for IOFile model.

Tests model creation, FileType enum, timestamps, constraints, and CRUD operations.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from psychrag.data.models.io_file import IOFile, FileType


class TestIOFileCreation:
    """Test basic model creation and field values."""

    def test_create_io_file_input(self, session):
        """Test creating IOFile with INPUT file type."""
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"
        )
        session.add(io_file)
        session.commit()

        assert io_file.id is not None
        assert io_file.filename == "test.pdf"
        assert io_file.file_type == FileType.INPUT
        assert io_file.file_path == "/path/to/test.pdf"
        assert isinstance(io_file.created_at, datetime)
        assert isinstance(io_file.updated_at, datetime)
        assert isinstance(io_file.last_seen_at, datetime)

    def test_create_io_file_to_convert(self, session):
        """Test creating IOFile with TO_CONVERT file type."""
        io_file = IOFile(
            filename="document.epub",
            file_type=FileType.TO_CONVERT,
            file_path="/path/to/document.epub"
        )
        session.add(io_file)
        session.commit()

        assert io_file.file_type == FileType.TO_CONVERT
        assert io_file.filename == "document.epub"

    def test_timestamps_auto_populate(self, session):
        """Test that timestamps are automatically populated."""
        before = datetime.now(timezone.utc)
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"
        )
        session.add(io_file)
        session.commit()
        after = datetime.now(timezone.utc)

        assert io_file.created_at is not None
        assert io_file.updated_at is not None
        assert io_file.last_seen_at is not None
        # SQLite returns naive datetimes, so convert to naive for comparison
        before_naive = before.replace(tzinfo=None)
        after_naive = after.replace(tzinfo=None)
        created_naive = io_file.created_at.replace(tzinfo=None) if io_file.created_at.tzinfo else io_file.created_at
        updated_naive = io_file.updated_at.replace(tzinfo=None) if io_file.updated_at.tzinfo else io_file.updated_at
        last_seen_naive = io_file.last_seen_at.replace(tzinfo=None) if io_file.last_seen_at.tzinfo else io_file.last_seen_at
        assert before_naive <= created_naive <= after_naive
        assert before_naive <= updated_naive <= after_naive
        assert before_naive <= last_seen_naive <= after_naive

    def test_repr(self, session):
        """Test __repr__ method."""
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"
        )
        session.add(io_file)
        session.commit()

        repr_str = repr(io_file)
        assert "IOFile" in repr_str
        assert "test.pdf" in repr_str
        assert "input" in repr_str.lower()


class TestFileTypeEnum:
    """Test FileType enum values."""

    def test_file_type_enum_values(self):
        """Test FileType enum has correct values."""
        assert FileType.INPUT == "input"
        assert FileType.TO_CONVERT == "to_convert"

    def test_file_type_enum_string_comparison(self):
        """Test FileType enum can be compared with strings."""
        assert FileType.INPUT == "input"
        assert FileType.TO_CONVERT == "to_convert"


class TestIOFileConstraints:
    """Test database constraints."""

    def test_unique_file_path_constraint(self, session):
        """Test that file_path must be unique."""
        io_file1 = IOFile(
            filename="test1.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"
        )
        session.add(io_file1)
        session.commit()

        # Attempt to create duplicate file_path
        io_file2 = IOFile(
            filename="test2.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"  # Same path
        )
        session.add(io_file2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_filename_required(self, session):
        """Test that filename is NOT NULL."""
        io_file = IOFile(
            filename=None,
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"
        )
        session.add(io_file)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_file_type_required(self, session):
        """Test that file_type is NOT NULL."""
        io_file = IOFile(
            filename="test.pdf",
            file_type=None,
            file_path="/path/to/test.pdf"
        )
        session.add(io_file)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_file_path_required(self, session):
        """Test that file_path is NOT NULL."""
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path=None
        )
        session.add(io_file)

        with pytest.raises(IntegrityError):
            session.commit()


class TestIOFileCRUD:
    """Test CRUD operations."""

    def test_create_io_file(self, session):
        """Test creating an IOFile."""
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"
        )
        session.add(io_file)
        session.commit()

        assert io_file.id is not None
        assert io_file.filename == "test.pdf"

    def test_read_io_file(self, session):
        """Test reading an IOFile."""
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"
        )
        session.add(io_file)
        session.commit()
        file_id = io_file.id

        # Retrieve
        retrieved = session.query(IOFile).filter(IOFile.id == file_id).first()
        assert retrieved is not None
        assert retrieved.filename == "test.pdf"
        assert retrieved.file_type == FileType.INPUT
        assert retrieved.file_path == "/path/to/test.pdf"

    def test_update_io_file(self, session):
        """Test updating an IOFile."""
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"
        )
        session.add(io_file)
        session.commit()

        original_updated_at = io_file.updated_at

        # Update filename and last_seen_at
        io_file.filename = "updated.pdf"
        new_last_seen = datetime.now(timezone.utc)
        io_file.last_seen_at = new_last_seen
        session.commit()

        assert io_file.filename == "updated.pdf"
        # SQLite returns naive datetimes, so compare timestamps or convert both to naive
        retrieved_naive = io_file.last_seen_at.replace(tzinfo=None) if io_file.last_seen_at.tzinfo else io_file.last_seen_at
        expected_naive = new_last_seen.replace(tzinfo=None)
        # Allow small difference due to database round-trip
        assert abs((retrieved_naive - expected_naive).total_seconds()) < 1

    def test_delete_io_file(self, session):
        """Test deleting an IOFile."""
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"
        )
        session.add(io_file)
        session.commit()
        file_id = io_file.id

        # Delete
        session.delete(io_file)
        session.commit()

        # Verify deleted
        retrieved = session.query(IOFile).filter(IOFile.id == file_id).first()
        assert retrieved is None

    def test_query_by_filename(self, session):
        """Test querying IOFile by filename."""
        io_file1 = IOFile(
            filename="test1.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test1.pdf"
        )
        io_file2 = IOFile(
            filename="test2.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test2.pdf"
        )
        session.add_all([io_file1, io_file2])
        session.commit()

        results = session.query(IOFile).filter(IOFile.filename == "test1.pdf").all()
        assert len(results) == 1
        assert results[0].filename == "test1.pdf"

    def test_query_by_file_type(self, session):
        """Test querying IOFile by file_type."""
        io_file1 = IOFile(
            filename="input.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/input.pdf"
        )
        io_file2 = IOFile(
            filename="convert.epub",
            file_type=FileType.TO_CONVERT,
            file_path="/path/to/convert.epub"
        )
        session.add_all([io_file1, io_file2])
        session.commit()

        input_files = session.query(IOFile).filter(IOFile.file_type == FileType.INPUT).all()
        assert len(input_files) == 1
        assert input_files[0].file_type == FileType.INPUT

        convert_files = session.query(IOFile).filter(IOFile.file_type == FileType.TO_CONVERT).all()
        assert len(convert_files) == 1
        assert convert_files[0].file_type == FileType.TO_CONVERT

    def test_query_by_file_path(self, session):
        """Test querying IOFile by file_path."""
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path="/unique/path/to/test.pdf"
        )
        session.add(io_file)
        session.commit()

        result = session.query(IOFile).filter(IOFile.file_path == "/unique/path/to/test.pdf").first()
        assert result is not None
        assert result.file_path == "/unique/path/to/test.pdf"


class TestIOFileTimestamps:
    """Test timestamp behavior."""

    def test_last_seen_at_updates(self, session):
        """Test that last_seen_at can be updated."""
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test.pdf"
        )
        session.add(io_file)
        session.commit()

        original_last_seen = io_file.last_seen_at

        # Update last_seen_at
        new_time = datetime.now(timezone.utc)
        io_file.last_seen_at = new_time
        session.commit()

        # SQLite returns naive datetimes, so compare timestamps or convert both to naive
        retrieved_naive = io_file.last_seen_at.replace(tzinfo=None) if io_file.last_seen_at.tzinfo else io_file.last_seen_at
        expected_naive = new_time.replace(tzinfo=None)
        # Allow small difference due to database round-trip
        assert abs((retrieved_naive - expected_naive).total_seconds()) < 1
        assert io_file.last_seen_at != original_last_seen

    def test_multiple_files_different_timestamps(self, session):
        """Test that multiple files have independent timestamps."""
        import time

        io_file1 = IOFile(
            filename="test1.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test1.pdf"
        )
        session.add(io_file1)
        session.commit()

        time.sleep(0.01)  # Small delay

        io_file2 = IOFile(
            filename="test2.pdf",
            file_type=FileType.INPUT,
            file_path="/path/to/test2.pdf"
        )
        session.add(io_file2)
        session.commit()

        # Timestamps should be different (or very close)
        assert io_file1.created_at <= io_file2.created_at

