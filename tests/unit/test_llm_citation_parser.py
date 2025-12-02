"""
Unit tests for LLM citation parser module.

Tests the llm_citation_parser.py module for citation parsing with LLM.

Usage:
    pytest tests/unit/test_llm_citation_parser.py -v
"""

import pytest
from unittest.mock import Mock, patch

from psychrag.utils.llm_citation_parser import (
    Citation,
    parse_citation_with_llm,
    _build_citation_prompt,
)


class TestCitationModel:
    """Tests for Citation Pydantic model."""

    def test_citation_all_fields_optional(self):
        """Test that Citation model accepts no fields."""
        citation = Citation()
        assert citation.title is None
        assert citation.authors is None
        assert citation.year is None
        assert citation.publisher is None
        assert citation.isbn is None
        assert citation.doi is None
        assert citation.container_title is None
        assert citation.volume is None
        assert citation.issue is None
        assert citation.pages is None
        assert citation.url is None
        assert citation.work_type is None

    def test_citation_with_partial_data(self):
        """Test Citation with only some fields populated."""
        citation = Citation(
            title="Test Title",
            authors=["Author One", "Author Two"],
            year=2020
        )
        assert citation.title == "Test Title"
        assert len(citation.authors) == 2
        assert citation.authors[0] == "Author One"
        assert citation.year == 2020
        assert citation.publisher is None
        assert citation.isbn is None

    def test_citation_year_validation_too_short(self):
        """Test that year must be at least 4 digits."""
        with pytest.raises(ValueError):
            Citation(year=999)

    def test_citation_year_validation_too_long(self):
        """Test that year cannot be more than 4 digits."""
        with pytest.raises(ValueError):
            Citation(year=10000)

    def test_citation_with_all_fields(self):
        """Test Citation with all fields populated."""
        citation = Citation(
            title="Prediction, perception and agency",
            authors=["Friston, K."],
            year=2012,
            publisher="Elsevier",
            isbn="978-1234567890",
            doi="10.1016/j.ijpsycho.2011.10.005",
            container_title="International Journal of Psychophysiology",
            volume="83",
            issue="2",
            pages="248-252",
            url="https://example.com",
            work_type="article"
        )
        assert citation.title == "Prediction, perception and agency"
        assert citation.authors == ["Friston, K."]
        assert citation.year == 2012
        assert citation.work_type == "article"


class TestBuildCitationPrompt:
    """Tests for prompt building function."""

    def test_prompt_includes_citation_text(self):
        """Test that prompt contains the citation text."""
        citation = "Smith, J. (2020). Title."
        prompt = _build_citation_prompt(citation, "APA")
        assert citation in prompt

    def test_prompt_includes_format(self):
        """Test that prompt mentions the citation format."""
        prompt = _build_citation_prompt("citation text", "MLA")
        assert "MLA" in prompt

    def test_prompt_has_json_structure(self):
        """Test that prompt specifies JSON output format."""
        prompt = _build_citation_prompt("citation", "APA")
        assert "JSON" in prompt or "json" in prompt

    def test_prompt_has_extraction_rules(self):
        """Test that prompt includes extraction rules."""
        prompt = _build_citation_prompt("citation", "Chicago")
        assert "authors" in prompt.lower()
        assert "year" in prompt.lower()
        assert "title" in prompt.lower()


class TestParseCitationWithLLM:
    """Tests for parse_citation_with_llm function."""

    @patch('psychrag.utils.llm_citation_parser.create_langchain_chat')
    @patch('psychrag.ai.config.LLMSettings')
    def test_parse_apa_citation_success(self, mock_settings_class, mock_create_chat):
        """Test successful parsing of APA citation."""
        # Mock LLM provider enum
        from psychrag.ai.config import LLMProvider

        # Mock LLM settings
        mock_settings = Mock()
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.get_model.return_value = "gpt-4o-mini"
        mock_settings_class.return_value = mock_settings

        # Mock LLM response
        expected_citation = Citation(
            title="Prediction, perception and agency",
            authors=["Friston, K."],
            year=2012,
            container_title="International Journal of Psychophysiology",
            volume="83",
            issue="2",
            pages="248-252",
            work_type="article"
        )

        mock_chat = Mock()
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = expected_citation
        mock_chat.with_structured_output.return_value = mock_structured_llm
        
        mock_stack = Mock()
        mock_stack.chat = mock_chat
        mock_create_chat.return_value = mock_stack

        # Test parsing
        citation_text = "Friston, K. (2012). Prediction, perception and agency. International Journal of Psychophysiology, 83(2), 248-252."
        result = parse_citation_with_llm(citation_text, "APA")

        assert result.title == "Prediction, perception and agency"
        assert result.year == 2012
        assert result.authors == ["Friston, K."]
        assert result.volume == "83"
        assert result.issue == "2"
        assert result.volume == "83"
        assert result.issue == "2"
        mock_structured_llm.invoke.assert_called_once()

    @patch('psychrag.utils.llm_citation_parser.create_langchain_chat')
    @patch('psychrag.ai.config.LLMSettings')
    def test_parse_mla_citation_success(self, mock_settings_class, mock_create_chat):
        """Test successful parsing of MLA citation."""
        # Mock LLM provider enum
        from psychrag.ai.config import LLMProvider

        # Mock LLM settings
        mock_settings = Mock()
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.get_model.return_value = "gpt-4o-mini"
        mock_settings_class.return_value = mock_settings

        expected_citation = Citation(
            title="Title",
            authors=["Smith, John"],
            year=2020,
            work_type="book"
        )

        mock_chat = Mock()
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = expected_citation
        mock_chat.with_structured_output.return_value = mock_structured_llm
        
        mock_stack = Mock()
        mock_stack.chat = mock_chat
        mock_create_chat.return_value = mock_stack

        citation_text = 'Smith, John. "Title." Publisher, 2020.'
        result = parse_citation_with_llm(citation_text, "MLA")

        assert result.title == "Title"
        assert result.year == 2020
        assert result.authors == ["Smith, John"]

    def test_parse_empty_citation_raises_error(self):
        """Test that empty citation text raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_citation_with_llm("", "APA")

        with pytest.raises(ValueError, match="cannot be empty"):
            parse_citation_with_llm("   ", "APA")

    def test_parse_invalid_format_raises_error(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported citation format"):
            parse_citation_with_llm("citation text", "INVALID")

    @patch('psychrag.utils.llm_citation_parser.create_langchain_chat')
    @patch('psychrag.ai.config.LLMSettings')
    def test_parse_handles_partial_data(self, mock_settings_class, mock_create_chat):
        """Test parsing with incomplete citation returns partial data."""
        # Mock LLM provider enum
        from psychrag.ai.config import LLMProvider

        # Mock LLM settings
        mock_settings = Mock()
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.get_model.return_value = "gpt-4o-mini"
        mock_settings_class.return_value = mock_settings

        expected_citation = Citation(
            title="Incomplete Citation",
            year=2020,
            # Other fields None
        )

        mock_chat = Mock()
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = expected_citation
        mock_chat.with_structured_output.return_value = mock_structured_llm
        
        mock_stack = Mock()
        mock_stack.chat = mock_chat
        mock_create_chat.return_value = mock_stack

        citation_text = "Incomplete citation, 2020."
        result = parse_citation_with_llm(citation_text, "APA")

        assert result.title == "Incomplete Citation"
        assert result.year == 2020
        assert result.authors is None
        assert result.publisher is None

    @patch('psychrag.utils.llm_citation_parser.create_langchain_chat')
    @patch('psychrag.ai.config.LLMSettings')
    def test_parse_llm_error_wrapped(self, mock_settings_class, mock_create_chat):
        """Test that LLM errors are wrapped with context."""
        # Mock LLM provider enum
        from psychrag.ai.config import LLMProvider

        # Mock LLM settings
        mock_settings = Mock()
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.get_model.return_value = "gpt-4o-mini"
        mock_settings_class.return_value = mock_settings

        mock_chat = Mock()
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.side_effect = Exception("LLM API error")
        mock_chat.with_structured_output.return_value = mock_structured_llm
        
        mock_stack = Mock()
        mock_stack.chat = mock_chat
        mock_create_chat.return_value = mock_stack

        with pytest.raises(ValueError, match="LLM citation parsing failed"):
            parse_citation_with_llm("citation", "APA")

    @patch('psychrag.utils.llm_citation_parser.create_langchain_chat')
    @patch('psychrag.ai.config.LLMSettings')
    def test_parse_chicago_citation(self, mock_settings_class, mock_create_chat):
        """Test parsing Chicago citation format."""
        # Mock LLM provider enum
        from psychrag.ai.config import LLMProvider

        # Mock LLM settings
        mock_settings = Mock()
        mock_settings.provider = LLMProvider.GEMINI
        mock_settings.get_model.return_value = "gemini-1.5-flash"
        mock_settings_class.return_value = mock_settings

        expected_citation = Citation(
            title="Cognitive Psychology: A Student's Handbook",
            authors=["Eysenck, Michael W.", "Keane, Mark T."],
            year=2020,
            publisher="Psychology Press",
            work_type="book"
        )

        mock_chat = Mock()
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = expected_citation
        mock_chat.with_structured_output.return_value = mock_structured_llm
        
        mock_stack = Mock()
        mock_stack.chat = mock_chat
        mock_create_chat.return_value = mock_stack

        citation_text = "Eysenck, Michael W., and Mark T. Keane. Cognitive Psychology: A Student's Handbook. 8th ed. Psychology Press, 2020."
        result = parse_citation_with_llm(citation_text, "Chicago")

        assert result.title == "Cognitive Psychology: A Student's Handbook"
        assert result.year == 2020
        assert len(result.authors) == 2
        assert result.publisher == "Psychology Press"


class TestIntegrationScenarios:
    """Integration test scenarios with realistic citations."""

    @patch('psychrag.utils.llm_citation_parser.create_langchain_chat')
    @patch('psychrag.ai.config.LLMSettings')
    def test_parse_journal_article_with_doi(self, mock_settings_class, mock_create_chat):
        """Test parsing journal article with DOI."""
        # Mock LLM provider enum
        from psychrag.ai.config import LLMProvider

        # Mock LLM settings
        mock_settings = Mock()
        mock_settings.provider = LLMProvider.OPENAI
        mock_settings.get_model.return_value = "gpt-4o-mini"
        mock_settings_class.return_value = mock_settings

        expected_citation = Citation(
            title="Relevance realization and the emerging framework in cognitive science",
            authors=["Vervaeke, John", "Lillicrap, Timothy P.", "Richards, Blake A."],
            year=2012,
            container_title="Journal of Logic and Computation",
            volume="22",
            issue="1",
            pages="79-99",
            doi="10.1093/logcom/exq041",
            work_type="article"
        )

        mock_chat = Mock()
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = expected_citation
        mock_chat.with_structured_output.return_value = mock_structured_llm
        
        mock_stack = Mock()
        mock_stack.chat = mock_chat
        mock_create_chat.return_value = mock_stack

        citation_text = 'Vervaeke, John, Timothy P. Lillicrap, and Blake A. Richards. "Relevance realization and the emerging framework in cognitive science." Journal of Logic and Computation 22.1 (2012): 79-99.'
        result = parse_citation_with_llm(citation_text, "MLA")

        assert result.title == "Relevance realization and the emerging framework in cognitive science"
        assert result.container_title == "Journal of Logic and Computation"
        assert len(result.authors) == 3
        assert result.doi is not None
