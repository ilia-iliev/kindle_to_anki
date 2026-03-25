import pytest
import requests
import time
from unittest.mock import Mock, patch
from dictionary_service import DictionaryService, DictionaryServiceError


class TestDictionaryService:
    """Test cases for DictionaryService class."""

    def test_init(self):
        """Test DictionaryService initialization."""
        service = DictionaryService()
        assert service.base_url == "https://api.dictionaryapi.dev/api/v2/entries/en"
        assert service.session is not None

    def test_get_definition_success(self):
        """Test successful word definition retrieval."""
        service = DictionaryService()

        # Test with a real word
        definition = service.get_definition("hello")

        assert definition is not None
        assert isinstance(definition, str)
        assert len(definition) > 0
        assert "hello" in definition.lower()

    def test_get_definition_word_not_found(self):
        """Test word definition retrieval for non-existent word."""
        service = DictionaryService()

        # Test with a made-up word
        definition = service.get_definition("xyzabc123")

        assert definition is None

    def test_get_definition_empty_word(self):
        """Test word definition retrieval with empty word."""
        service = DictionaryService()

        with pytest.raises(ValueError, match="Word cannot be empty"):
            service.get_definition("")

    def test_get_definition_none_word(self):
        """Test word definition retrieval with None word."""
        service = DictionaryService()

        with pytest.raises(ValueError, match="Word cannot be None"):
            service.get_definition(None)

    def test_get_definition_network_error(self):
        """Test word definition retrieval with network error."""
        service = DictionaryService()

        with patch.object(
            service.session,
            "get",
            side_effect=requests.RequestException("Network error"),
        ):
            with pytest.raises(
                DictionaryServiceError, match="Failed to fetch definition"
            ):
                service.get_definition("hello")

    def test_get_definition_invalid_response(self):
        """Test word definition retrieval with invalid response."""
        service = DictionaryService()

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("Server error")

        with patch.object(service.session, "get", return_value=mock_response):
            with pytest.raises(
                DictionaryServiceError, match="Failed to fetch definition"
            ):
                service.get_definition("hello")

    def test_get_definition_multiple_words(self):
        """Test getting definitions for multiple words."""
        service = DictionaryService()

        words = ["hello", "world", "test"]
        definitions = service.get_definitions(words)

        assert len(definitions) == len(words)
        assert all(isinstance(d, str) for d in definitions if d is not None)

    def test_get_definition_special_characters(self):
        """Test word definition retrieval with special characters."""
        service = DictionaryService()

        # Test with words containing special characters
        definition = service.get_definition("café")

        assert definition is not None
        assert isinstance(definition, str)

    def test_get_definition_case_insensitive(self):
        """Test word definition retrieval is case insensitive."""
        service = DictionaryService()

        definition_lower = service.get_definition("hello")
        definition_upper = service.get_definition("HELLO")

        # Both should return the same definition
        assert definition_lower == definition_upper

    def test_clean_word(self):
        """Test word cleaning functionality."""
        service = DictionaryService()

        assert service._clean_word("  hello  ") == "hello"
        assert service._clean_word("HELLO") == "hello"
        assert service._clean_word("Hello-World") == "hello-world"
        assert service._clean_word("hello123") == "hello123"

    def test_rate_limiting_respects_max_requests_per_second(self):
        """Test that rate limiting enforces maximum 10 requests per second."""
        service = DictionaryService()

        start_time = time.time()

        # Make 10 requests quickly
        for i in range(10):
            service.get_definition(f"test{i}")

        # The 11th request should be delayed to respect rate limit
        eleventh_start = time.time()
        service.get_definition("test11")
        eleventh_end = time.time()

        # Should take at least 0.1 seconds (1/10th of a second for rate limiting)
        assert eleventh_end - eleventh_start >= 0.09  # Allow small tolerance

    def test_retry_logic_on_temporary_failure(self):
        """Test that retry logic works for temporary failures."""
        service = DictionaryService()

        # Mock response that fails twice then succeeds
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = [
            {"meanings": [{"definitions": [{"definition": "test definition"}]}]}
        ]

        mock_response_failure = Mock()
        mock_response_failure.status_code = 503
        mock_response_failure.raise_for_status.side_effect = requests.HTTPError(
            "Service unavailable"
        )

        with patch.object(
            service.session,
            "get",
            side_effect=[
                mock_response_failure,
                mock_response_failure,
                mock_response_success,
            ],
        ):
            definition = service.get_definition("test")

            assert definition == "1. test definition"
            # Verify it was called 3 times (2 failures + 1 success)
            assert service.session.get.call_count == 3

    def test_retry_logic_gives_up_after_max_retries(self):
        """Test that retry logic gives up after maximum 3 retries."""
        service = DictionaryService()

        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "Service unavailable"
        )

        with patch.object(service.session, "get", return_value=mock_response):
            with pytest.raises(
                DictionaryServiceError, match="Failed to fetch definition"
            ):
                service.get_definition("test")

            # Verify it was called exactly 4 times (initial + 3 retries)
            assert service.session.get.call_count == 4

    def test_retry_logic_with_exponential_backoff(self):
        """Test that retry logic uses exponential backoff."""
        service = DictionaryService()

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = [
            {"meanings": [{"definitions": [{"definition": "test definition"}]}]}
        ]

        mock_response_failure = Mock()
        mock_response_failure.status_code = 503
        mock_response_failure.raise_for_status.side_effect = requests.HTTPError(
            "Service unavailable"
        )

        with (
            patch.object(
                service.session,
                "get",
                side_effect=[
                    mock_response_failure,
                    mock_response_failure,
                    mock_response_success,
                ],
            ),
            patch("time.sleep") as mock_sleep,
        ):
            service.get_definition("test")

            # Verify sleep was called with increasing delays
            assert mock_sleep.call_count == 2
            # First retry should wait ~1 second, second retry ~2 seconds
            assert mock_sleep.call_args_list[0][0][0] >= 0.9  # Allow tolerance
            assert mock_sleep.call_args_list[1][0][0] >= 1.9  # Allow tolerance

    def test_rate_limiting_in_bulk_operations(self):
        """Test that rate limiting works correctly in bulk operations."""
        service = DictionaryService()

        start_time = time.time()

        # Make 15 requests in bulk
        words = [f"word{i}" for i in range(15)]
        definitions = service.get_definitions(words)

        end_time = time.time()

        # Should take at least 1.0 seconds (15 requests / 10 per second = 1.5 seconds, but some might be 404s)
        assert end_time - start_time >= 1.0
        assert len(definitions) == 15

    def test_retry_logic_does_not_retry_on_404(self):
        """Test that retry logic does not retry on 404 (word not found)."""
        service = DictionaryService()

        mock_response = Mock()
        mock_response.status_code = 404

        with patch.object(service.session, "get", return_value=mock_response):
            definition = service.get_definition("nonexistentword")

            assert definition is None
            # Should only be called once (no retries for 404)
            assert service.session.get.call_count == 1

    def test_retry_logic_does_not_retry_on_400(self):
        """Test that retry logic retries on 400 (bad request) as it might be temporary."""
        service = DictionaryService()

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.HTTPError("Bad request")

        with patch.object(service.session, "get", return_value=mock_response):
            with pytest.raises(DictionaryServiceError):
                service.get_definition("test")

            # Should be called 4 times (initial + 3 retries)
            assert service.session.get.call_count == 4

    def test_extract_definition_with_word_category(self):
        """Test that definitions include word category (part of speech)."""
        service = DictionaryService()

        # Mock response with part of speech
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "meanings": [
                    {
                        "partOfSpeech": "verb",
                        "definitions": [{"definition": "To move swiftly on foot"}],
                    }
                ]
            }
        ]

        with patch.object(service.session, "get", return_value=mock_response):
            definition = service.get_definition("run")
            assert definition == "(v) 1. To move swiftly on foot"

    def test_extract_definition_with_multiple_definitions(self):
        """Test that multiple definitions are included and numbered."""
        service = DictionaryService()

        # Mock response with multiple definitions
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [
                            {"definition": "Act of running"},
                            {"definition": "A journey or trip"},
                            {"definition": "A flow of liquid"},
                        ],
                    }
                ]
            }
        ]

        with patch.object(service.session, "get", return_value=mock_response):
            definition = service.get_definition("run")
            expected = "(n) 1. Act of running\n(n) 2. A journey or trip\n(n) 3. A flow of liquid"
            assert definition == expected

    def test_extract_definition_with_multiple_parts_of_speech(self):
        """Test that definitions from different parts of speech are included."""
        service = DictionaryService()

        # Mock response with multiple parts of speech
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "meanings": [
                    {
                        "partOfSpeech": "verb",
                        "definitions": [{"definition": "To move swiftly"}],
                    },
                    {
                        "partOfSpeech": "noun",
                        "definitions": [{"definition": "Act of running"}],
                    },
                    {
                        "partOfSpeech": "adjective",
                        "definitions": [{"definition": "In a liquid state"}],
                    },
                ]
            }
        ]

        with patch.object(service.session, "get", return_value=mock_response):
            definition = service.get_definition("run")
            expected = "(v) 1. To move swiftly\n(n) 2. Act of running\n(adj) 3. In a liquid state"
            assert definition == expected

    def test_extract_definition_removes_quotes(self):
        """Test that quotes are removed from definitions."""
        service = DictionaryService()

        # Mock response with quoted definition
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [{"definition": '"A person who runs"'}],
                    }
                ]
            }
        ]

        with patch.object(service.session, "get", return_value=mock_response):
            definition = service.get_definition("runner")
            assert definition == "(n) 1. A person who runs"

    def test_extract_definition_with_complex_quotes(self):
        """Test that complex quote patterns are handled correctly."""
        service = DictionaryService()

        # Mock response with complex quotes
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "meanings": [
                    {
                        "partOfSpeech": "noun",
                        "definitions": [
                            {"definition": '"Hello" means "greeting"'},
                            {"definition": "A word without quotes"},
                        ],
                    }
                ]
            }
        ]

        with patch.object(service.session, "get", return_value=mock_response):
            definition = service.get_definition("hello")
            expected = "(n) 1. Hello means greeting\n(n) 2. A word without quotes"
            assert definition == expected

    def test_extract_definition_handles_empty_definitions(self):
        """Test that empty or missing definitions are handled gracefully."""
        service = DictionaryService()

        # Mock response with empty definitions
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"meanings": [{"partOfSpeech": "noun", "definitions": []}]}
        ]

        with patch.object(service.session, "get", return_value=mock_response):
            definition = service.get_definition("test")
            assert definition is None

    def test_extract_definition_handles_missing_part_of_speech(self):
        """Test that missing part of speech is handled gracefully."""
        service = DictionaryService()

        # Mock response without part of speech
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"meanings": [{"definitions": [{"definition": "A test definition"}]}]}
        ]

        with patch.object(service.session, "get", return_value=mock_response):
            definition = service.get_definition("test")
            assert definition == "1. A test definition"

    def test_extract_definition_handles_malformed_response(self):
        """Test that malformed API responses are handled gracefully."""
        service = DictionaryService()

        # Mock malformed response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"meanings": "not a list"}]

        with patch.object(service.session, "get", return_value=mock_response):
            definition = service.get_definition("test")
            assert definition is None
