"""
Unit tests for prompt template API endpoints.

Tests CRUD operations for template management via REST API.

Usage:
    pytest tests/unit/test_templates_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Generator

from psychrag_api.main import app
from psychrag.data.database import get_session, get_db_session
from psychrag.data.models.prompt_template import PromptTemplate


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """Create a database session for testing."""
    with get_session() as session:
        yield session
        # Rollback any changes after test
        session.rollback()


@pytest.fixture
def client(session: Session):
    """Create test client with database dependency override."""
    # Override the get_db_session dependency to use our test session
    def override_get_db_session():
        yield session
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    try:
        test_client = TestClient(app)
        yield test_client
    finally:
        # Clean up dependency override after test (even if test fails)
        app.dependency_overrides.clear()


@pytest.fixture
def sample_templates(session: Session):
    """Create sample templates for testing."""
    templates = [
        PromptTemplate(
            function_tag="test_function",
            version=1,
            title="Test Template V1",
            template_content="Test template with {variable}",
            is_active=True
        ),
        PromptTemplate(
            function_tag="test_function",
            version=2,
            title="Test Template V2",
            template_content="Updated template with {variable}",
            is_active=False
        ),
        PromptTemplate(
            function_tag="another_function",
            version=1,
            title="Another Function V1",
            template_content="Another template with {param}",
            is_active=True
        ),
    ]
    session.add_all(templates)
    session.commit()
    yield templates
    # Cleanup: Delete test templates
    try:
        session.query(PromptTemplate).filter(
            PromptTemplate.function_tag.in_(["test_function", "another_function"])
        ).delete(synchronize_session=False)
        session.commit()
    except Exception:
        session.rollback()


class TestListAllTemplates:
    """Test GET /settings/templates/"""

    def test_list_all_templates_empty(self, client, session):
        """Test listing templates when database is empty."""
        # Clear all templates
        session.query(PromptTemplate).delete()
        session.commit()

        response = client.get("/settings/templates/")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) == 0

    def test_list_all_templates(self, client, sample_templates):
        """Test listing all templates grouped by function_tag."""
        response = client.get("/settings/templates/")
        assert response.status_code == 200
        data = response.json()

        assert "templates" in data
        assert len(data["templates"]) == 2  # Two function tags

        # Verify structure
        for func_summary in data["templates"]:
            assert "function_tag" in func_summary
            assert "active_version" in func_summary
            assert "versions" in func_summary

    def test_list_shows_active_version(self, client, sample_templates):
        """Test that active version is correctly identified."""
        response = client.get("/settings/templates/")
        assert response.status_code == 200
        data = response.json()

        # Find test_function
        test_func = next(
            t for t in data["templates"]
            if t["function_tag"] == "test_function"
        )

        assert test_func["active_version"] == 1
        assert len(test_func["versions"]) == 2

        # Verify version details
        active_version = next(v for v in test_func["versions"] if v["is_active"])
        assert active_version["version"] == 1


class TestGetTemplatesForFunction:
    """Test GET /settings/templates/{function_tag}"""

    def test_get_templates_for_function(self, client, sample_templates):
        """Test retrieving all versions for a function."""
        response = client.get("/settings/templates/test_function")
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        assert all(t["function_tag"] == "test_function" for t in data)

    def test_get_templates_for_function_not_found(self, client, sample_templates):
        """Test 404 for unknown function_tag."""
        response = client.get("/settings/templates/nonexistent")
        assert response.status_code == 404
        assert "No templates found" in response.json()["detail"]

    def test_get_templates_ordered_by_version(self, client, sample_templates):
        """Test that versions are in descending order."""
        response = client.get("/settings/templates/test_function")
        assert response.status_code == 200
        data = response.json()

        versions = [t["version"] for t in data]
        assert versions == [2, 1]  # Descending order


class TestGetSpecificVersion:
    """Test GET /settings/templates/{function_tag}/{version}"""

    def test_get_specific_version(self, client, sample_templates):
        """Test retrieving a specific version."""
        response = client.get("/settings/templates/test_function/1")
        assert response.status_code == 200
        data = response.json()

        assert data["function_tag"] == "test_function"
        assert data["version"] == 1
        assert data["title"] == "Test Template V1"
        assert data["template_content"] == "Test template with {variable}"
        assert data["is_active"] is True

    def test_get_version_not_found(self, client, sample_templates):
        """Test 404 for non-existent version."""
        response = client.get("/settings/templates/test_function/999")
        assert response.status_code == 404
        assert "Template not found" in response.json()["detail"]

    def test_get_version_wrong_function(self, client, sample_templates):
        """Test 404 when version exists but for different function."""
        response = client.get("/settings/templates/nonexistent/1")
        assert response.status_code == 404


class TestCreateNewVersion:
    """Test POST /settings/templates/{function_tag}"""

    def test_create_first_version(self, client, session):
        """Test creating v1 when no templates exist for function."""
        # Clear any existing templates for new_function
        session.query(PromptTemplate).filter(
            PromptTemplate.function_tag == "new_function"
        ).delete()
        session.commit()

        try:
            response = client.post(
                "/settings/templates/new_function",
                json={
                    "title": "New Function V1",
                    "template_content": "New template with {param}"
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert data["version"] == 1
            assert data["is_active"] is False
            assert data["title"] == "New Function V1"
        finally:
            # Cleanup: Delete test templates
            try:
                session.query(PromptTemplate).filter(
                    PromptTemplate.function_tag == "new_function"
                ).delete(synchronize_session=False)
                session.commit()
            except Exception:
                session.rollback()

    def test_create_auto_increment_version(self, client, sample_templates):
        """Test that version auto-increments correctly."""
        response = client.post(
            "/settings/templates/test_function",
            json={
                "title": "Test Template V3",
                "template_content": "New template with {variable}"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["version"] == 3
        assert data["is_active"] is False
        assert data["title"] == "Test Template V3"

    def test_create_new_version_not_active(self, client, sample_templates):
        """Test that new versions default to inactive."""
        response = client.post(
            "/settings/templates/test_function",
            json={
                "title": "Test Template V3",
                "template_content": "Template with {variable}"
            }
        )

        assert response.status_code == 201
        assert response.json()["is_active"] is False

    def test_create_invalid_template_format(self, client, sample_templates):
        """Test validation for invalid PromptTemplate format."""
        response = client.post(
            "/settings/templates/test_function",
            json={
                "title": "Invalid Template",
                "template_content": "Template with unclosed brace {"
            }
        )

        assert response.status_code == 422  # Validation error
        # Pydantic validation errors return 422


class TestUpdateTemplate:
    """Test PUT /settings/templates/{function_tag}/{version}"""

    def test_update_template_content(self, client, sample_templates):
        """Test updating template content."""
        response = client.put(
            "/settings/templates/test_function/1",
            json={
                "template_content": "Modified template with {variable}"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["template_content"] == "Modified template with {variable}"
        assert data["title"] == "Test Template V1"  # Unchanged

    def test_update_template_title(self, client, sample_templates):
        """Test updating template title."""
        response = client.put(
            "/settings/templates/test_function/1",
            json={
                "title": "Modified Title"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Modified Title"

    def test_update_both_fields(self, client, sample_templates):
        """Test updating both title and content."""
        response = client.put(
            "/settings/templates/test_function/1",
            json={
                "title": "New Title",
                "template_content": "New content with {variable}"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["template_content"] == "New content with {variable}"

    def test_update_template_not_found(self, client, sample_templates):
        """Test 404 for non-existent template."""
        response = client.put(
            "/settings/templates/test_function/999",
            json={
                "template_content": "Content"
            }
        )

        assert response.status_code == 404

    def test_update_invalid_template_format(self, client, sample_templates):
        """Test validation for invalid PromptTemplate format."""
        response = client.put(
            "/settings/templates/test_function/1",
            json={
                "template_content": "Invalid {{"
            }
        )

        assert response.status_code == 422  # Validation error


class TestActivateVersion:
    """Test PUT /settings/templates/{function_tag}/{version}/activate"""

    def test_activate_version(self, client, sample_templates, session):
        """Test activating a version."""
        response = client.put("/settings/templates/test_function/2/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == 2
        assert data["is_active"] is True

    def test_activate_deactivates_others(self, client, sample_templates, session):
        """Test that activating one version deactivates others."""
        # Activate version 2
        client.put("/settings/templates/test_function/2/activate")

        # Check version 1 is now inactive
        response = client.get("/settings/templates/test_function/1")
        assert response.status_code == 200
        assert response.json()["is_active"] is False

        # Check version 2 is active
        response = client.get("/settings/templates/test_function/2")
        assert response.status_code == 200
        assert response.json()["is_active"] is True

    def test_activate_only_affects_same_function(self, client, sample_templates):
        """Test that activation doesn't affect other function_tags."""
        # Activate version 2 of test_function
        client.put("/settings/templates/test_function/2/activate")

        # Check another_function is unaffected
        response = client.get("/settings/templates/another_function/1")
        assert response.status_code == 200
        assert response.json()["is_active"] is True

    def test_activate_not_found(self, client, sample_templates):
        """Test 404 for non-existent version."""
        response = client.put("/settings/templates/test_function/999/activate")

        assert response.status_code == 404
        assert "Template not found" in response.json()["detail"]

    def test_activate_already_active(self, client, sample_templates):
        """Test activating an already-active version (should succeed)."""
        response = client.put("/settings/templates/test_function/1/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True


class TestTemplateValidation:
    """Test template validation with various formats."""

    @pytest.fixture(autouse=True)
    def cleanup_validation_templates(self, session: Session):
        """Clean up validation_test templates after each test."""
        yield
        # Cleanup
        try:
            session.query(PromptTemplate).filter(
                PromptTemplate.function_tag == "validation_test"
            ).delete(synchronize_session=False)
            session.commit()
        except Exception:
            session.rollback()

    def test_valid_template_single_variable(self, client, session):
        """Test template with single variable."""
        response = client.post(
            "/settings/templates/validation_test",
            json={
                "title": "Single Variable",
                "template_content": "Hello {name}"
            }
        )

        assert response.status_code == 201

    def test_valid_template_multiple_variables(self, client, session):
        """Test template with multiple variables."""
        response = client.post(
            "/settings/templates/validation_test",
            json={
                "title": "Multiple Variables",
                "template_content": "User {name} is {age} years old and lives in {city}"
            }
        )

        assert response.status_code == 201

    def test_valid_template_no_variables(self, client, session):
        """Test template with no variables (valid)."""
        response = client.post(
            "/settings/templates/validation_test",
            json={
                "title": "No Variables",
                "template_content": "This is a static template"
            }
        )

        assert response.status_code == 201
