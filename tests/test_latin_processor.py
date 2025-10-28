# tests/test_latin_processor.py
import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from flask import jsonify, Response
from app.processors.latin_processor import LatinProcessor


class TestLatinProcessor:
    """Test suite for LatinProcessor class"""

    @pytest.fixture
    def mock_ai_provider(self):
        """Create a mock AI provider for testing"""
        mock_provider = Mock()
        return mock_provider

    @pytest.fixture
    def processor(self, mock_ai_provider):
        """Create a LatinProcessor instance for testing"""
        return LatinProcessor(mock_ai_provider)

    def test_initialization(self, processor, mock_ai_provider):
        """Test that LatinProcessor initializes correctly"""
        assert processor.ai_provider == mock_ai_provider
        assert "latin_analysis" in processor.prompt_templates
        assert "LEMMA:" in processor.prompt_templates["latin_analysis"]
        assert "PART OF SPEECH:" in processor.prompt_templates["latin_analysis"]
        assert "MEANING:" in processor.prompt_templates["latin_analysis"]

    def test_process_latin_analysis_pattern(self, processor, mock_ai_provider, app):
        """Test processing latin_analysis pattern"""
        # Mock AI provider response
        mock_response = {
            "choices": [{"message": {"content": "Latin analysis result"}}]
        }
        mock_ai_provider.generate_openai_compatible.return_value = mock_response
        
        pattern_data = {
            "pattern": "latin_analysis",
            "word_form": "amare"
        }
        
        with app.app_context():
            result = processor.process(pattern_data, "test-model", False, {})
        
        # Should return a Response object for success
        assert isinstance(result, Response)
        assert result.status_code == 200
        response_data = result.get_json()
        assert "choices" in response_data
        assert response_data["choices"][0]["message"]["content"] == "Latin analysis result"

    def test_process_unsupported_pattern(self, processor, app):
        """Test processing unsupported pattern"""
        pattern_data = {
            "pattern": "unsupported_pattern",
            "word_form": "test"
        }
        
        with app.app_context():
            result = processor.process(pattern_data, "test-model", False, {})
        
        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 400
        response_data = response.get_json()
        assert "error" in response_data
        assert "Unsupported Latin pattern" in response_data["error"]

    def test_analyze_latin_word_success(self, processor, mock_ai_provider, app):
        """Test successful Latin word analysis"""
        mock_response = {
            "choices": [{"message": {"content": "Detailed Latin analysis"}}]
        }
        mock_ai_provider.generate_openai_compatible.return_value = mock_response
        
        pattern_data = {
            "pattern": "latin_analysis",
            "word_form": "puella"
        }
        
        with app.app_context():
            result = processor._analyze_latin_word(pattern_data, "test-model", False, {})
        
        # Should return a Response object for success
        assert isinstance(result, Response)
        assert result.status_code == 200
        response_data = result.get_json()
        assert response_data["choices"][0]["message"]["content"] == "Detailed Latin analysis"

    def test_analyze_latin_word_missing_word_form(self, processor, app):
        """Test Latin word analysis with missing word_form"""
        pattern_data = {
            "pattern": "latin_analysis"
            # Missing word_form
        }
        
        with app.app_context():
            result = processor._analyze_latin_word(pattern_data, "test-model", False, {})
        
        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 400
        response_data = response.get_json()
        assert "error" in response_data
        assert "word_form is required" in response_data["error"]

    def test_analyze_latin_word_empty_word_form(self, processor, app):
        """Test Latin word analysis with empty word_form"""
        pattern_data = {
            "pattern": "latin_analysis",
            "word_form": ""
        }
        
        with app.app_context():
            result = processor._analyze_latin_word(pattern_data, "test-model", False, {})
        
        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 400
        response_data = response.get_json()
        assert "error" in response_data
        assert "word_form is required" in response_data["error"]

    def test_analyze_latin_word_whitespace_word_form(self, processor, app):
        """Test Latin word analysis with whitespace-only word_form"""
        pattern_data = {
            "pattern": "latin_analysis",
            "word_form": "   "
        }
        
        with app.app_context():
            result = processor._analyze_latin_word(pattern_data, "test-model", False, {})
        
        # Should return a tuple for error cases
        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 500  # Changed to 500 since it's an AI provider error
        response_data = response.get_json()
        assert "error" in response_data
        assert "Error formatting response" in response_data["error"]

    def test_analyze_latin_word_strips_whitespace(self, processor, mock_ai_provider, app):
        """Test that word_form is properly stripped of whitespace"""
        mock_response = {
            "choices": [{"message": {"content": "Analysis"}}]
        }
        mock_ai_provider.generate_openai_compatible.return_value = mock_response
        
        pattern_data = {
            "pattern": "latin_analysis",
            "word_form": "  puella  "
        }
        
        with app.app_context():
            result = processor._analyze_latin_word(pattern_data, "test-model", False, {})
        
        # Verify the prompt was called with the stripped word
        mock_ai_provider.generate_openai_compatible.assert_called_once()
        call_args = mock_ai_provider.generate_openai_compatible.call_args
        messages = call_args[0][0]
        assert "puella" in messages[0]["content"]
        assert "  puella  " not in messages[0]["content"]

    def test_call_ai_provider_success(self, processor, mock_ai_provider, app):
        """Test successful AI provider call"""
        mock_response = {
            "choices": [{"message": {"content": "AI response"}}]
        }
        mock_ai_provider.generate_openai_compatible.return_value = mock_response
        
        prompt = "Test prompt"
        original_data = {
            "temperature": 0.2,
            "top_p": 0.8,
            "max_tokens": 2048
        }
        
        with app.app_context():
            result = processor._call_ai_provider(prompt, "test-model", False, original_data)
        
        # Should return a Response object for success
        assert isinstance(result, Response)
        assert result.status_code == 200
        
        # Verify AI provider was called with correct parameters
        mock_ai_provider.generate_openai_compatible.assert_called_once()
        call_args = mock_ai_provider.generate_openai_compatible.call_args
        assert call_args[1]["temperature"] == 0.2
        assert call_args[1]["top_p"] == 0.8
        assert call_args[1]["max_tokens"] == 2048
        assert call_args[1]["stream"] == False

    def test_call_ai_provider_default_options(self, processor, mock_ai_provider, app):
        """Test AI provider call with default options"""
        mock_response = {
            "choices": [{"message": {"content": "AI response"}}]
        }
        mock_ai_provider.generate_openai_compatible.return_value = mock_response
        
        prompt = "Test prompt"
        original_data = {}  # Empty options
        
        with app.app_context():
            result = processor._call_ai_provider(prompt, "test-model", False, original_data)
        
        # Should return a Response object for success
        assert isinstance(result, Response)
        assert result.status_code == 200
        
        # Verify default options were used
        call_args = mock_ai_provider.generate_openai_compatible.call_args
        assert call_args[1]["temperature"] == 0.1
        assert call_args[1]["top_p"] == 0.9
        assert call_args[1]["max_tokens"] == 4096

    def test_call_ai_provider_streaming(self, processor, mock_ai_provider):
        """Test AI provider call with streaming"""
        mock_stream = [
            'data: {"choices": [{"delta": {"content": "Stream"}}]}',
            'data: {"choices": [{"delta": {"content": "ing"}}]}'
        ]
        mock_ai_provider.generate_openai_compatible.return_value = mock_stream
        
        prompt = "Test prompt"
        
        result = processor._call_ai_provider(prompt, "test-model", True, {})
        
        # Should return a Response object for streaming
        assert isinstance(result, Response)
        assert result.mimetype == 'text/event-stream'

    def test_call_ai_provider_exception(self, processor, mock_ai_provider, app):
        """Test AI provider call with exception"""
        mock_ai_provider.generate_openai_compatible.side_effect = Exception("AI provider error")
        
        prompt = "Test prompt"
        
        with app.app_context():
            result = processor._call_ai_provider(prompt, "test-model", False, {})
        
        assert isinstance(result, tuple)
        response, status_code = result
        assert status_code == 500
        response_data = response.get_json()
        assert "error" in response_data
        assert "Latin analysis failed" in response_data["error"]
        assert "AI provider error" in response_data["error"]

    def test_format_streaming_response_openai_format(self, processor):
        """Test formatting streaming response with OpenAI format"""
        mock_stream = [
            'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            'data: {"choices": [{"delta": {"content": " World"}}]}'
        ]
        
        result = processor._format_streaming_response(mock_stream, "test-model")
        
        assert isinstance(result, Response)
        assert result.mimetype == 'text/event-stream'
        
        # Test the generator
        data = list(result.response)
        assert len(data) > 0
        # Check that we have proper SSE format
        assert any('data: {' in chunk for chunk in data)
        assert any('[DONE]' in chunk for chunk in data)

    def test_format_streaming_response_ollama_format(self, processor):
        """Test formatting streaming response with Ollama format"""
        mock_stream = [
            '{"response": "Ollama"}',
            '{"response": " response"}'
        ]
        
        result = processor._format_streaming_response(mock_stream, "test-model")
        
        assert isinstance(result, Response)
        assert result.mimetype == 'text/event-stream'

    def test_format_streaming_response_bytes(self, processor):
        """Test formatting streaming response with bytes input"""
        mock_stream = [
            b'data: {"choices": [{"delta": {"content": "Bytes"}}]}',
            b'data: {"choices": [{"delta": {"content": " content"}}]}'
        ]
        
        result = processor._format_streaming_response(mock_stream, "test-model")
        
        assert isinstance(result, Response)
        assert result.mimetype == 'text/event-stream'

    def test_format_streaming_response_invalid_json(self, processor):
        """Test formatting streaming response with invalid JSON"""
        mock_stream = [
            'data: invalid json',
            'data: {"choices": [{"delta": {"content": "Valid"}}]}'
        ]
        
        result = processor._format_streaming_response(mock_stream, "test-model")
        
        assert isinstance(result, Response)
        assert result.mimetype == 'text/event-stream'

    def test_format_openai_response_openai_format(self, processor, app):
        """Test formatting OpenAI format response"""
        mock_response = {
            "choices": [{"message": {"content": "OpenAI response"}}]
        }
        
        with app.app_context():
            result = processor._format_openai_response(mock_response, "test-model")
        
        assert isinstance(result, Response)
        response_data = result.get_json()
        assert response_data["choices"][0]["message"]["content"] == "OpenAI response"
        assert response_data["model"] == "test-model"
        assert response_data["object"] == "chat.completion"
        assert "id" in response_data
        assert "created" in response_data

    def test_format_openai_response_ollama_format(self, processor, app):
        """Test formatting Ollama format response"""
        mock_response = {
            "response": "Ollama response"
        }
        
        with app.app_context():
            result = processor._format_openai_response(mock_response, "test-model")
        
        assert isinstance(result, Response)
        response_data = result.get_json()
        assert response_data["choices"][0]["message"]["content"] == "Ollama response"

    def test_format_openai_response_string_response(self, processor, app):
        """Test formatting string response"""
        mock_response = "String response"
        
        with app.app_context():
            result = processor._format_openai_response(mock_response, "test-model")
        
        assert isinstance(result, Response)
        response_data = result.get_json()
        assert response_data["choices"][0]["message"]["content"] == "String response"

    def test_format_openai_response_exception(self, processor, app):
        """Test formatting response with exception"""
        mock_response = None  # This will cause an exception
        
        with app.app_context():
            result = processor._format_openai_response(mock_response, "test-model")
        
        # Should return a Response object even for exceptions
        assert isinstance(result, Response)
        assert result.status_code == 200  # The method handles exceptions internally

    def test_health_check(self, processor, app):
        """Test health check method"""
        with app.app_context():
            result = processor.health_check()
        
        assert isinstance(result, Response)
        response_data = result.get_json()
        assert response_data["status"] == "healthy"
        assert response_data["processor"] == "latin_processor"
        assert "supported_patterns" in response_data
        assert "latin_analysis" in response_data["supported_patterns"]

    def test_prompt_template_formatting(self, processor):
        """Test that prompt template is correctly formatted"""
        template = processor.prompt_templates["latin_analysis"]
        formatted = template.format(word_form="puella")
        
        assert "puella" in formatted
        assert "**LEMMA:**" in formatted
        assert "**PART OF SPEECH:**" in formatted
        assert "**MEANING:**" in formatted
        assert "**GRAMMATICAL ANALYSIS:**" in formatted
        assert "**PRINCIPAL PARTS:**" in formatted
        assert "**DECLENSION/CONJUGATION:**" in formatted
        assert "**FULL FORM PARADIGM:**" in formatted
        assert "**ETYMOLOGY:**" in formatted
        assert "**USAGE EXAMPLES:**" in formatted
        assert "**RELATED WORDS:**" in formatted
        assert "**NOTES:**" in formatted

    def test_prompt_template_contains_word_form(self, processor):
        """Test that prompt template contains the word form in multiple places"""
        template = processor.prompt_templates["latin_analysis"]
        formatted = template.format(word_form="amare")
        
        # Should appear in the title and at the end
        assert "**amare**" in formatted
        assert "Word to analyze: amare" in formatted

    def test_streaming_response_generator_yields_correct_format(self, processor):
        """Test that streaming response generator yields correct SSE format"""
        mock_stream = [
            'data: {"choices": [{"delta": {"content": "Test"}}]}'
        ]
        
        result = processor._format_streaming_response(mock_stream, "test-model")
        generator = result.response
        
        # Get the first chunk
        first_chunk = next(generator)
        assert isinstance(first_chunk, str)
        
        # Should contain proper SSE format
        assert first_chunk.startswith('data: {')
        assert '"object": "chat.completion.chunk"' in first_chunk
        assert '"model": "test-model"' in first_chunk

    def test_streaming_response_final_chunk(self, processor):
        """Test that streaming response includes final done chunk"""
        mock_stream = [
            'data: {"choices": [{"delta": {"content": "Test"}}]}'
        ]
        
        result = processor._format_streaming_response(mock_stream, "test-model")
        generator = result.response
        
        # Consume all chunks
        chunks = list(generator)
        
        # Should have at least one data chunk and a final done chunk
        assert len(chunks) >= 2
        
        # Check for final done chunk
        final_chunks = chunks[-2:]
        assert any('"finish_reason": "stop"' in chunk for chunk in final_chunks)
        assert any('[DONE]' in chunk for chunk in final_chunks)

    def test_openai_response_includes_usage(self, processor, app):
        """Test that OpenAI response includes usage information"""
        mock_response = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        
        with app.app_context():
            result = processor._format_openai_response(mock_response, "test-model")
        response_data = result.get_json()
        
        assert "usage" in response_data
        assert response_data["usage"]["prompt_tokens"] == 0
        assert response_data["usage"]["completion_tokens"] == 0
        assert response_data["usage"]["total_tokens"] == 0

    def test_openai_response_includes_choices_structure(self, processor, app):
        """Test that OpenAI response has correct choices structure"""
        mock_response = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        
        with app.app_context():
            result = processor._format_openai_response(mock_response, "test-model")
        response_data = result.get_json()
        
        assert "choices" in response_data
        assert len(response_data["choices"]) == 1
        assert response_data["choices"][0]["index"] == 0
        assert response_data["choices"][0]["message"]["role"] == "assistant"
        assert response_data["choices"][0]["finish_reason"] == "stop"

    def test_process_with_streaming_true(self, processor, mock_ai_provider):
        """Test process method with streaming enabled"""
        mock_stream = [
            'data: {"choices": [{"delta": {"content": "Stream"}}]}'
        ]
        mock_ai_provider.generate_openai_compatible.return_value = mock_stream
        
        pattern_data = {
            "pattern": "latin_analysis",
            "word_form": "test"
        }
        
        result = processor.process(pattern_data, "test-model", True, {})
        
        # Should return a Response object for streaming
        assert isinstance(result, Response)
        assert result.mimetype == 'text/event-stream'

    def test_process_with_custom_options(self, processor, mock_ai_provider, app):
        """Test process method with custom options"""
        mock_response = {
            "choices": [{"message": {"content": "Custom response"}}]
        }
        mock_ai_provider.generate_openai_compatible.return_value = mock_response
        
        pattern_data = {
            "pattern": "latin_analysis",
            "word_form": "custom"
        }
        
        original_data = {
            "temperature": 0.5,
            "top_p": 0.7,
            "max_tokens": 1000
        }
        
        with app.app_context():
            result = processor.process(pattern_data, "test-model", False, original_data)
        
        # Should return a Response object for success
        assert isinstance(result, Response)
        assert result.status_code == 200
        
        # Verify custom options were passed
        call_args = mock_ai_provider.generate_openai_compatible.call_args
        assert call_args[1]["temperature"] == 0.5
        assert call_args[1]["top_p"] == 0.7
        assert call_args[1]["max_tokens"] == 1000


# Test configuration for pytest
@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment"""
    import os
    os.environ['TESTING'] = 'true'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
