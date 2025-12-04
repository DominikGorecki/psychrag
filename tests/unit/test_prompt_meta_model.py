"""
Unit tests for PromptMeta model.

Tests model creation, JSONB variables field, variable_dict property,
from_variables_list method, and CRUD operations.
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from psychrag.data.models.prompt_meta import PromptMeta


class TestPromptMetaCreation:
    """Test basic model creation and field values."""

    def test_create_prompt_meta_basic(self, session):
        """Test creating a PromptMeta with basic fields."""
        meta = PromptMeta(
            function_tag="test_function",
            variables=[]
        )
        session.add(meta)
        session.commit()

        assert meta.id is not None
        assert meta.function_tag == "test_function"
        assert meta.variables == []
        assert isinstance(meta.created_at, datetime)
        assert isinstance(meta.updated_at, datetime)

    def test_create_prompt_meta_with_variables(self, session):
        """Test creating a PromptMeta with variables."""
        variables = [
            {"variable_name": "query", "variable_description": "User's search query"},
            {"variable_name": "context", "variable_description": "Retrieved documents"}
        ]
        meta = PromptMeta(
            function_tag="test_function",
            variables=variables
        )
        session.add(meta)
        session.commit()

        assert meta.variables == variables
        assert len(meta.variables) == 2

    def test_repr(self, session):
        """Test __repr__ method."""
        meta = PromptMeta(
            function_tag="test_function",
            variables=[
                {"variable_name": "var1", "variable_description": "Desc 1"},
                {"variable_name": "var2", "variable_description": "Desc 2"}
            ]
        )
        session.add(meta)
        session.commit()

        repr_str = repr(meta)
        assert "PromptMeta" in repr_str
        assert "test_function" in repr_str
        assert "2" in repr_str  # Number of variables


class TestPromptMetaVariableDict:
    """Test variable_dict property."""

    def test_variable_dict_empty(self, session):
        """Test variable_dict with empty variables."""
        meta = PromptMeta(
            function_tag="test_function",
            variables=[]
        )
        session.add(meta)
        session.commit()

        assert meta.variable_dict == {}

    def test_variable_dict_conversion(self, session):
        """Test variable_dict converts variables list to dictionary."""
        variables = [
            {"variable_name": "query", "variable_description": "User's search query"},
            {"variable_name": "context", "variable_description": "Retrieved documents"},
            {"variable_name": "n", "variable_description": "Number of queries"}
        ]
        meta = PromptMeta(
            function_tag="test_function",
            variables=variables
        )
        session.add(meta)
        session.commit()

        var_dict = meta.variable_dict
        assert isinstance(var_dict, dict)
        assert var_dict["query"] == "User's search query"
        assert var_dict["context"] == "Retrieved documents"
        assert var_dict["n"] == "Number of queries"

    def test_variable_dict_missing_fields(self, session):
        """Test variable_dict handles variables with missing fields."""
        variables = [
            {"variable_name": "query", "variable_description": "Description"},
            {"variable_name": "context"},  # Missing variable_description
            {"variable_description": "Description only"},  # Missing variable_name
            {"variable_name": "valid", "variable_description": "Valid var"}
        ]
        meta = PromptMeta(
            function_tag="test_function",
            variables=variables
        )
        session.add(meta)
        session.commit()

        var_dict = meta.variable_dict
        # Should only include variables with both fields
        assert "query" in var_dict
        assert "valid" in var_dict
        assert "context" not in var_dict  # Missing description
        assert len(var_dict) == 2

    def test_variable_dict_non_dict_items(self, session):
        """Test variable_dict handles non-dict items in variables list."""
        variables = [
            {"variable_name": "query", "variable_description": "Description"},
            "not a dict",  # Invalid item
            123,  # Invalid item
            {"variable_name": "valid", "variable_description": "Valid"}
        ]
        meta = PromptMeta(
            function_tag="test_function",
            variables=variables
        )
        session.add(meta)
        session.commit()

        var_dict = meta.variable_dict
        # Should only include valid dict items
        assert "query" in var_dict
        assert "valid" in var_dict
        assert len(var_dict) == 2


class TestPromptMetaFromVariablesList:
    """Test from_variables_list class method."""

    def test_from_variables_list_basic(self):
        """Test creating PromptMeta from variables list."""
        variables = [
            {"variable_name": "query", "variable_description": "User's search query"},
            {"variable_name": "context", "variable_description": "Retrieved documents"}
        ]
        meta = PromptMeta.from_variables_list("test_function", variables)

        assert meta.function_tag == "test_function"
        assert meta.variables == variables
        assert len(meta.variables) == 2

    def test_from_variables_list_empty(self):
        """Test from_variables_list with empty list."""
        meta = PromptMeta.from_variables_list("test_function", [])

        assert meta.function_tag == "test_function"
        assert meta.variables == []

    def test_from_variables_list_single_variable(self):
        """Test from_variables_list with single variable."""
        variables = [
            {"variable_name": "query", "variable_description": "User query"}
        ]
        meta = PromptMeta.from_variables_list("single_var", variables)

        assert meta.function_tag == "single_var"
        assert len(meta.variables) == 1
        assert meta.variables[0]["variable_name"] == "query"


class TestPromptMetaConstraints:
    """Test database constraints."""

    def test_unique_function_tag_constraint(self, session):
        """Test that function_tag must be unique."""
        meta1 = PromptMeta(
            function_tag="test_function",
            variables=[]
        )
        session.add(meta1)
        session.commit()

        # Attempt to create duplicate function_tag
        meta2 = PromptMeta(
            function_tag="test_function",  # Same function_tag
            variables=[{"variable_name": "var", "variable_description": "Desc"}]
        )
        session.add(meta2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_function_tag_required(self, session):
        """Test that function_tag is NOT NULL."""
        meta = PromptMeta(
            function_tag=None,
            variables=[]
        )
        session.add(meta)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_variables_required(self, session):
        """Test that variables is NOT NULL and has proper defaults."""
        # Test ORM-level validation - validator runs during object initialization
        with pytest.raises(ValueError, match="variables cannot be None"):
            meta = PromptMeta(
                function_tag="test_function",
                variables=None
            )
        
        # Test database-level default: omitting the column should use DEFAULT '[]'::jsonb
        from sqlalchemy import insert
        stmt = insert(PromptMeta.__table__).values(
            function_tag="test_function2"
            # variables omitted - should use database default
        )
        
        session.execute(stmt)
        session.commit()
        
        # Verify that default empty list was applied
        result = session.query(PromptMeta).filter(
            PromptMeta.function_tag == "test_function2"
        ).first()
        assert result is not None
        assert result.variables == []  # Default value applied


class TestPromptMetaCRUD:
    """Test CRUD operations."""

    def test_create_prompt_meta(self, session):
        """Test creating a PromptMeta."""
        meta = PromptMeta(
            function_tag="create_test",
            variables=[{"variable_name": "var1", "variable_description": "Desc 1"}]
        )
        session.add(meta)
        session.commit()

        assert meta.id is not None
        assert meta.function_tag == "create_test"

    def test_read_prompt_meta(self, session):
        """Test reading a PromptMeta."""
        meta = PromptMeta(
            function_tag="read_test",
            variables=[{"variable_name": "var1", "variable_description": "Desc 1"}]
        )
        session.add(meta)
        session.commit()
        meta_id = meta.id

        # Retrieve
        retrieved = session.query(PromptMeta).filter(PromptMeta.id == meta_id).first()
        assert retrieved is not None
        assert retrieved.function_tag == "read_test"
        assert len(retrieved.variables) == 1

    def test_update_prompt_meta(self, session):
        """Test updating a PromptMeta."""
        meta = PromptMeta(
            function_tag="update_test",
            variables=[{"variable_name": "var1", "variable_description": "Original"}]
        )
        session.add(meta)
        session.commit()

        # Update variables
        new_variables = [
            {"variable_name": "var1", "variable_description": "Updated"},
            {"variable_name": "var2", "variable_description": "New var"}
        ]
        meta.variables = new_variables
        session.commit()

        assert len(meta.variables) == 2
        assert meta.variables[0]["variable_description"] == "Updated"
        assert meta.variables[1]["variable_name"] == "var2"

    def test_delete_prompt_meta(self, session):
        """Test deleting a PromptMeta."""
        meta = PromptMeta(
            function_tag="delete_test",
            variables=[]
        )
        session.add(meta)
        session.commit()
        meta_id = meta.id

        # Delete
        session.delete(meta)
        session.commit()

        # Verify deleted
        retrieved = session.query(PromptMeta).filter(PromptMeta.id == meta_id).first()
        assert retrieved is None

    def test_query_by_function_tag(self, session):
        """Test querying PromptMeta by function_tag."""
        meta1 = PromptMeta(
            function_tag="function1",
            variables=[]
        )
        meta2 = PromptMeta(
            function_tag="function2",
            variables=[]
        )
        session.add_all([meta1, meta2])
        session.commit()

        result = session.query(PromptMeta).filter(
            PromptMeta.function_tag == "function1"
        ).first()

        assert result is not None
        assert result.function_tag == "function1"


class TestPromptMetaTimestamps:
    """Test timestamp behavior."""

    def test_timestamps_auto_populate(self, session):
        """Test that timestamps are automatically populated."""
        before = datetime.now()
        meta = PromptMeta(
            function_tag="timestamp_test",
            variables=[]
        )
        session.add(meta)
        session.commit()
        after = datetime.now()

        assert meta.created_at is not None
        assert meta.updated_at is not None
        # Note: Exact comparison depends on timezone handling

    def test_multiple_meta_different_timestamps(self, session):
        """Test that multiple PromptMeta instances have independent timestamps."""
        import time

        meta1 = PromptMeta(
            function_tag="meta1",
            variables=[]
        )
        session.add(meta1)
        session.commit()

        time.sleep(0.01)  # Small delay

        meta2 = PromptMeta(
            function_tag="meta2",
            variables=[]
        )
        session.add(meta2)
        session.commit()

        # Timestamps should be different (or very close)
        assert meta1.created_at <= meta2.created_at

