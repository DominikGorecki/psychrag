"""
Unit tests for PromptTemplate model.

Tests model creation, validation, constraints, and queries.
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from psychrag.data.models.prompt_template import PromptTemplate


class TestPromptTemplateCreation:
    """Test basic model creation and field values."""

    def test_create_prompt_template(self, session):
        """Test creating a PromptTemplate instance with all fields."""
        template = PromptTemplate(
            function_tag="test_function",
            version=1,
            title="Test Template V1",
            template_content="Test template with {variable}",
            is_active=True
        )
        session.add(template)
        session.commit()

        # Verify all fields are set
        assert template.id is not None
        assert template.function_tag == "test_function"
        assert template.version == 1
        assert template.title == "Test Template V1"
        assert template.template_content == "Test template with {variable}"
        assert template.is_active is True
        assert isinstance(template.created_at, datetime)
        assert isinstance(template.updated_at, datetime)

    def test_default_values(self, session):
        """Test that is_active defaults to FALSE and timestamps auto-populate."""
        template = PromptTemplate(
            function_tag="test_function",
            version=1,
            title="Test Template",
            template_content="Test content"
            # is_active not specified
        )
        session.add(template)
        session.commit()

        # Verify defaults
        assert template.is_active is False
        assert template.created_at is not None
        assert template.updated_at is not None

    def test_repr(self, session):
        """Test __repr__ method."""
        template = PromptTemplate(
            function_tag="test_function",
            version=2,
            title="Test",
            template_content="Content",
            is_active=True
        )
        session.add(template)
        session.commit()

        repr_str = repr(template)
        assert "PromptTemplate" in repr_str
        assert "test_function" in repr_str
        assert "version=2" in repr_str
        assert "active=True" in repr_str


class TestPromptTemplateValidation:
    """Test model validation logic."""

    def test_version_validation_positive(self, session):
        """Test that positive version numbers are accepted."""
        template = PromptTemplate(
            function_tag="test",
            version=1,
            title="Test",
            template_content="Content"
        )
        session.add(template)
        session.commit()

        assert template.version == 1

    def test_version_validation_zero(self, session):
        """Test that version=0 raises ValueError."""
        with pytest.raises(ValueError, match="Version must be greater than 0"):
            template = PromptTemplate(
                function_tag="test",
                version=0,
                title="Test",
                template_content="Content"
            )
            session.add(template)
            session.flush()  # Trigger validation

    def test_version_validation_negative(self, session):
        """Test that negative version raises ValueError."""
        with pytest.raises(ValueError, match="Version must be greater than 0"):
            template = PromptTemplate(
                function_tag="test",
                version=-1,
                title="Test",
                template_content="Content"
            )
            session.add(template)
            session.flush()  # Trigger validation


class TestPromptTemplateConstraints:
    """Test database constraints (requires test DB)."""

    def test_unique_constraint(self, session):
        """Test that duplicate (function_tag, version) fails."""
        # Create first template
        template1 = PromptTemplate(
            function_tag="test_function",
            version=1,
            title="Version 1",
            template_content="Content 1"
        )
        session.add(template1)
        session.commit()

        # Attempt to create duplicate
        template2 = PromptTemplate(
            function_tag="test_function",
            version=1,  # Same version
            title="Duplicate",
            template_content="Content 2"
        )
        session.add(template2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_function_tag_required(self, session):
        """Test that function_tag is NOT NULL."""
        template = PromptTemplate(
            function_tag=None,
            version=1,
            title="Test",
            template_content="Content"
        )
        session.add(template)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_template_content_required(self, session):
        """Test that template_content is NOT NULL."""
        template = PromptTemplate(
            function_tag="test",
            version=1,
            title="Test",
            template_content=None
        )
        session.add(template)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_check_constraint_version_positive(self, session):
        """Test CHECK constraint enforces version > 0."""
        # Note: SQLAlchemy validator catches this first, but the DB constraint is also there
        with pytest.raises((ValueError, IntegrityError)):
            template = PromptTemplate(
                function_tag="test",
                version=0,
                title="Test",
                template_content="Content"
            )
            session.add(template)
            session.commit()


class TestPromptTemplateQueries:
    """Test querying templates."""

    @pytest.fixture
    def sample_templates(self, session):
        """Create sample templates for testing."""
        templates = [
            PromptTemplate(
                function_tag="query_expansion",
                version=1,
                title="Query Expansion V1",
                template_content="Template V1 with {query}",
                is_active=False
            ),
            PromptTemplate(
                function_tag="query_expansion",
                version=2,
                title="Query Expansion V2",
                template_content="Template V2 with {query}",
                is_active=True
            ),
            PromptTemplate(
                function_tag="rag_augmentation",
                version=1,
                title="RAG Augmentation V1",
                template_content="RAG template with {context}",
                is_active=True
            ),
        ]
        session.add_all(templates)
        session.commit()
        return templates

    def test_query_by_function_tag(self, session, sample_templates):
        """Test retrieving all templates for a function_tag."""
        templates = session.query(PromptTemplate).filter(
            PromptTemplate.function_tag == "query_expansion"
        ).all()

        assert len(templates) == 2
        assert all(t.function_tag == "query_expansion" for t in templates)

    def test_query_active_template(self, session, sample_templates):
        """Test retrieving the active template for a function_tag."""
        active = session.query(PromptTemplate).filter(
            PromptTemplate.function_tag == "query_expansion",
            PromptTemplate.is_active == True
        ).first()

        assert active is not None
        assert active.version == 2
        assert active.is_active is True

    def test_query_specific_version(self, session, sample_templates):
        """Test retrieving a specific version."""
        template = session.query(PromptTemplate).filter(
            PromptTemplate.function_tag == "query_expansion",
            PromptTemplate.version == 1
        ).first()

        assert template is not None
        assert template.version == 1
        assert template.title == "Query Expansion V1"

    def test_query_no_results(self, session, sample_templates):
        """Test querying non-existent function_tag returns None."""
        result = session.query(PromptTemplate).filter(
            PromptTemplate.function_tag == "nonexistent"
        ).first()

        assert result is None

    def test_query_multiple_functions(self, session, sample_templates):
        """Test querying multiple function tags."""
        all_templates = session.query(PromptTemplate).all()

        assert len(all_templates) == 3

        function_tags = {t.function_tag for t in all_templates}
        assert "query_expansion" in function_tags
        assert "rag_augmentation" in function_tags


class TestPromptTemplateLangChainCompatibility:
    """Test compatibility with LangChain PromptTemplate."""

    def test_langchain_template_loading(self, session):
        """Test that stored templates can be loaded as LangChain PromptTemplates."""
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate

        # Create template with valid LangChain syntax
        template = PromptTemplate(
            function_tag="test",
            version=1,
            title="Test",
            template_content="Hello {name}, you are {age} years old."
        )
        session.add(template)
        session.commit()

        # Load as LangChain PromptTemplate
        lc_template = LCPromptTemplate.from_template(template.template_content)

        # Test formatting
        result = lc_template.format(name="Alice", age=30)
        assert "Hello Alice" in result
        assert "30 years old" in result

    def test_langchain_template_with_multiple_variables(self, session):
        """Test LangChain template with multiple variables."""
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate

        template = PromptTemplate(
            function_tag="test",
            version=1,
            title="Test",
            template_content="Query: {query}, Number: {n}, Context: {context}"
        )
        session.add(template)
        session.commit()

        lc_template = LCPromptTemplate.from_template(template.template_content)
        result = lc_template.format(query="test query", n=5, context="test context")

        assert "test query" in result
        assert "5" in result
        assert "test context" in result


class TestPromptTemplateUpdates:
    """Test updating templates."""

    def test_update_template_content(self, session):
        """Test updating template_content."""
        template = PromptTemplate(
            function_tag="test",
            version=1,
            title="Original",
            template_content="Original content"
        )
        session.add(template)
        session.commit()

        original_updated_at = template.updated_at

        # Update content
        template.template_content = "Updated content"
        session.commit()

        # Verify update
        assert template.template_content == "Updated content"
        # Note: updated_at auto-update depends on SQLAlchemy configuration

    def test_toggle_active_status(self, session):
        """Test changing is_active status."""
        template = PromptTemplate(
            function_tag="test",
            version=1,
            title="Test",
            template_content="Content",
            is_active=False
        )
        session.add(template)
        session.commit()

        assert template.is_active is False

        # Activate
        template.is_active = True
        session.commit()

        assert template.is_active is True
