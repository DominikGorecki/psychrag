"""
Unit tests for delete_conversion module.

Tests conversion deletion, cascade deletion handling, and error cases.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from psychrag.sanitization.delete_conversion import delete_conversion
from psychrag.data.models.io_file import IOFile, FileType


class TestDeleteConversion:
    """Test conversion deletion functionality."""

    @patch('psychrag.sanitization.delete_conversion.load_config')
    @patch('psychrag.sanitization.delete_conversion.get_session')
    def test_delete_conversion_success(
        self, mock_get_session, mock_load_config, session, tmp_path
    ):
        """Test successful deletion of conversion files and database entry."""
        # Create test files in temporary output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        base_name = "test_book"
        test_files = [
            output_dir / f"{base_name}.pdf",
            output_dir / f"{base_name}.md",
            output_dir / f"{base_name}.style.md",
            output_dir / f"{base_name}.hier.md",
            output_dir / f"{base_name}.toc_titles.md",
        ]
        
        # Create the test files
        for file_path in test_files:
            file_path.write_text("test content")
            assert file_path.exists()
        
        # Create IOFile in database
        io_file = IOFile(
            filename=f"{base_name}.pdf",
            file_type=FileType.TO_CONVERT,
            file_path=str(output_dir / f"{base_name}.pdf")
        )
        session.add(io_file)
        session.commit()
        io_file_id = io_file.id
        
        # Mock get_session to return our test session
        mock_get_session.return_value.__enter__.return_value = session
        mock_get_session.return_value.__exit__.return_value = None
        
        # Mock load_config to return our temporary output directory
        mock_config = MagicMock()
        mock_config.paths.output_dir = str(output_dir)
        mock_load_config.return_value = mock_config
        
        # Execute deletion
        result = delete_conversion(io_file_id, verbose=False)
        
        # Verify result
        assert result["success"] is True
        assert len(result["deleted_files"]) == 5
        assert result["io_file_deleted"] is True
        assert base_name in result["message"]
        
        # Verify all files were deleted
        for file_path in test_files:
            assert not file_path.exists(), f"File {file_path.name} should have been deleted"
        
        # Verify database entry was deleted
        deleted_io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
        assert deleted_io_file is None, "IOFile entry should have been deleted from database"
        
        # Verify correct files were deleted
        deleted_filenames = set(result["deleted_files"])
        expected_filenames = {f.name for f in test_files}
        assert deleted_filenames == expected_filenames

    @patch('psychrag.sanitization.delete_conversion.load_config')
    @patch('psychrag.sanitization.delete_conversion.get_session')
    def test_delete_conversion_no_matching_files(
        self, mock_get_session, mock_load_config, session, tmp_path
    ):
        """Test deletion when no matching files exist in output directory."""
        # Create empty output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Create IOFile in database
        io_file = IOFile(
            filename="test_book.pdf",
            file_type=FileType.TO_CONVERT,
            file_path=str(output_dir / "test_book.pdf")
        )
        session.add(io_file)
        session.commit()
        io_file_id = io_file.id
        
        # Mock get_session
        mock_get_session.return_value.__enter__.return_value = session
        mock_get_session.return_value.__exit__.return_value = None
        
        # Mock load_config
        mock_config = MagicMock()
        mock_config.paths.output_dir = str(output_dir)
        mock_load_config.return_value = mock_config
        
        # Execute deletion
        result = delete_conversion(io_file_id, verbose=False)
        
        # Verify result - should succeed even with no files
        assert result["success"] is True
        assert len(result["deleted_files"]) == 0
        assert result["io_file_deleted"] is True
        
        # Verify database entry was deleted
        deleted_io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
        assert deleted_io_file is None

    @patch('psychrag.sanitization.delete_conversion.load_config')
    @patch('psychrag.sanitization.delete_conversion.get_session')
    def test_delete_conversion_verbose_mode(
        self, mock_get_session, mock_load_config, session, tmp_path, capsys
    ):
        """Test deletion with verbose mode enabled."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        base_name = "verbose_test"
        test_file = output_dir / f"{base_name}.md"
        test_file.write_text("test content")
        
        io_file = IOFile(
            filename=f"{base_name}.pdf",
            file_type=FileType.TO_CONVERT,
            file_path=str(output_dir / f"{base_name}.pdf")
        )
        session.add(io_file)
        session.commit()
        io_file_id = io_file.id
        
        mock_get_session.return_value.__enter__.return_value = session
        mock_get_session.return_value.__exit__.return_value = None
        
        mock_config = MagicMock()
        mock_config.paths.output_dir = str(output_dir)
        mock_load_config.return_value = mock_config
        
        # Execute deletion with verbose=True
        result = delete_conversion(io_file_id, verbose=True)
        
        # Verify verbose output
        captured = capsys.readouterr()
        assert "Base name:" in captured.out
        assert "IO File ID:" in captured.out
        assert "Found" in captured.out or "files to delete" in captured.out
        assert "Deleted:" in captured.out or "Deleted io_file entry" in captured.out
        
        assert result["success"] is True


class TestDeleteConversionErrorHandling:
    """Test error handling in delete_conversion."""

    @patch('psychrag.sanitization.delete_conversion.get_session')
    def test_delete_conversion_io_file_not_found(self, mock_get_session, session):
        """Test error handling when IOFile ID is not found."""
        mock_get_session.return_value.__enter__.return_value = session
        mock_get_session.return_value.__exit__.return_value = None
        
        # Try to delete non-existent IOFile
        with pytest.raises(ValueError, match="IOFile with ID 999 not found"):
            delete_conversion(999, verbose=False)

    @patch('psychrag.sanitization.delete_conversion.load_config')
    @patch('psychrag.sanitization.delete_conversion.get_session')
    def test_delete_conversion_invalid_filename_no_extension(
        self, mock_get_session, mock_load_config, session, tmp_path
    ):
        """Test error handling when filename has no extension."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Create IOFile with invalid filename (no extension)
        io_file = IOFile(
            filename="noextension",
            file_type=FileType.TO_CONVERT,
            file_path=str(output_dir / "noextension")
        )
        session.add(io_file)
        session.commit()
        io_file_id = io_file.id
        
        mock_get_session.return_value.__enter__.return_value = session
        mock_get_session.return_value.__exit__.return_value = None
        
        mock_config = MagicMock()
        mock_config.paths.output_dir = str(output_dir)
        mock_load_config.return_value = mock_config
        
        # Should raise ValueError for invalid filename format
        with pytest.raises(ValueError, match="Invalid filename format.*no extension found"):
            delete_conversion(io_file_id, verbose=False)

    @patch('psychrag.sanitization.delete_conversion.load_config')
    @patch('psychrag.sanitization.delete_conversion.get_session')
    def test_delete_conversion_output_dir_not_exists(
        self, mock_get_session, mock_load_config, session, tmp_path
    ):
        """Test error handling when output directory does not exist."""
        # Create IOFile in database
        io_file = IOFile(
            filename="test.pdf",
            file_type=FileType.TO_CONVERT,
            file_path="/some/path/test.pdf"
        )
        session.add(io_file)
        session.commit()
        io_file_id = io_file.id
        
        mock_get_session.return_value.__enter__.return_value = session
        mock_get_session.return_value.__exit__.return_value = None
        
        # Mock config with non-existent directory
        non_existent_dir = tmp_path / "nonexistent"
        mock_config = MagicMock()
        mock_config.paths.output_dir = str(non_existent_dir)
        mock_load_config.return_value = mock_config
        
        # Should raise ValueError for missing output directory
        with pytest.raises(ValueError, match="Output directory does not exist"):
            delete_conversion(io_file_id, verbose=False)

    @patch('psychrag.sanitization.delete_conversion.load_config')
    @patch('psychrag.sanitization.delete_conversion.get_session')
    def test_delete_conversion_file_deletion_error_handled(
        self, mock_get_session, mock_load_config, session, tmp_path, monkeypatch
    ):
        """Test that file deletion errors are handled gracefully."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        base_name = "test_book"
        test_file = output_dir / f"{base_name}.md"
        test_file.write_text("test content")
        
        io_file = IOFile(
            filename=f"{base_name}.pdf",
            file_type=FileType.TO_CONVERT,
            file_path=str(output_dir / f"{base_name}.pdf")
        )
        session.add(io_file)
        session.commit()
        io_file_id = io_file.id
        
        mock_get_session.return_value.__enter__.return_value = session
        mock_get_session.return_value.__exit__.return_value = None
        
        mock_config = MagicMock()
        mock_config.paths.output_dir = str(output_dir)
        mock_load_config.return_value = mock_config
        
        # Mock unlink to raise an exception for one file
        original_unlink = Path.unlink
        call_count = [0]
        
        def mock_unlink(self):
            call_count[0] += 1
            if call_count[0] == 1:
                raise PermissionError("Cannot delete file")
            return original_unlink(self)
        
        monkeypatch.setattr(Path, "unlink", mock_unlink)
        
        # Execute deletion - should still succeed but handle the error
        result = delete_conversion(io_file_id, verbose=False)
        
        # Should still report success and delete database entry
        assert result["success"] is True
        assert result["io_file_deleted"] is True
        
        # Database entry should still be deleted
        deleted_io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
        assert deleted_io_file is None


class TestDeleteConversionCascadeDeletion:
    """Test cascade deletion behavior."""
    
    @patch('psychrag.sanitization.delete_conversion.load_config')
    @patch('psychrag.sanitization.delete_conversion.get_session')
    def test_delete_conversion_only_deletes_matching_base_name(
        self, mock_get_session, mock_load_config, session, tmp_path
    ):
        """Test that only files with matching base name are deleted."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        base_name = "book1"
        other_base_name = "book2"
        
        # Create files for book1
        book1_files = [
            output_dir / f"{base_name}.pdf",
            output_dir / f"{base_name}.md",
        ]
        
        # Create files for book2 (should NOT be deleted)
        book2_files = [
            output_dir / f"{other_base_name}.pdf",
            output_dir / f"{other_base_name}.md",
        ]
        
        # Create all files
        for file_path in book1_files + book2_files:
            file_path.write_text("test content")
        
        # Create IOFile for book1 only
        io_file = IOFile(
            filename=f"{base_name}.pdf",
            file_type=FileType.TO_CONVERT,
            file_path=str(output_dir / f"{base_name}.pdf")
        )
        session.add(io_file)
        session.commit()
        io_file_id = io_file.id
        
        mock_get_session.return_value.__enter__.return_value = session
        mock_get_session.return_value.__exit__.return_value = None
        
        mock_config = MagicMock()
        mock_config.paths.output_dir = str(output_dir)
        mock_load_config.return_value = mock_config
        
        # Execute deletion
        result = delete_conversion(io_file_id, verbose=False)
        
        # Verify only book1 files were deleted
        for file_path in book1_files:
            assert not file_path.exists(), f"{file_path.name} should have been deleted"
        
        # Verify book2 files still exist
        for file_path in book2_files:
            assert file_path.exists(), f"{file_path.name} should NOT have been deleted"
        
        # Verify deleted_files only contains book1 files
        deleted_filenames = set(result["deleted_files"])
        expected_filenames = {f.name for f in book1_files}
        assert deleted_filenames == expected_filenames

    @patch('psychrag.sanitization.delete_conversion.load_config')
    @patch('psychrag.sanitization.delete_conversion.get_session')
    def test_delete_conversion_multiple_extensions(
        self, mock_get_session, mock_load_config, session, tmp_path
    ):
        """Test deletion of files with various extensions."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        base_name = "complex_book"
        test_files = [
            output_dir / f"{base_name}.pdf",
            output_dir / f"{base_name}.md",
            output_dir / f"{base_name}.style.md",
            output_dir / f"{base_name}.hier.md",
            output_dir / f"{base_name}.toc_titles.md",
            output_dir / f"{base_name}.sanitized.md",
            output_dir / f"{base_name}.vec_sugg.md",
        ]
        
        for file_path in test_files:
            file_path.write_text("test content")
        
        io_file = IOFile(
            filename=f"{base_name}.pdf",
            file_type=FileType.TO_CONVERT,
            file_path=str(output_dir / f"{base_name}.pdf")
        )
        session.add(io_file)
        session.commit()
        io_file_id = io_file.id
        
        mock_get_session.return_value.__enter__.return_value = session
        mock_get_session.return_value.__exit__.return_value = None
        
        mock_config = MagicMock()
        mock_config.paths.output_dir = str(output_dir)
        mock_load_config.return_value = mock_config
        
        result = delete_conversion(io_file_id, verbose=False)
        
        # Verify all files with base_name were deleted
        assert len(result["deleted_files"]) == len(test_files)
        for file_path in test_files:
            assert not file_path.exists()
        
        # Verify database entry was deleted
        deleted_io_file = session.query(IOFile).filter(IOFile.id == io_file_id).first()
        assert deleted_io_file is None
