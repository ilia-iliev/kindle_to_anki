import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
from frequent_words import FrequentWordsManager


class TestFrequentWordsManager:
    """Test cases for FrequentWordsManager class."""

    def test_download_frequent_words(self):
        """Test downloading frequent words from internet."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "frequent_words.json")
            manager = FrequentWordsManager(cache_file)

            # Mock the internet request
            with patch("frequent_words.requests.get") as mock_get:
                mock_response = MagicMock()
                mock_response.text = "the\nbe\nto\nof\nand\nin\nthat\nhave\nit\nfor"
                mock_response.status_code = 200
                mock_get.return_value = mock_response

                words = manager.download_frequent_words()

                assert len(words) == 10
                assert "the" in words
                assert "be" in words
                assert "to" in words
                mock_get.assert_called_once()

    def test_save_words_to_cache(self):
        """Test saving words to local cache file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "frequent_words.json")
            manager = FrequentWordsManager(cache_file)

            test_words = ["the", "be", "to", "of", "and"]
            manager.save_words_to_cache(test_words)

            # Check that file was created
            assert os.path.exists(cache_file)

            # Check file contents
            with open(cache_file, "r") as f:
                data = json.load(f)

            assert data["words"] == test_words
            assert "last_updated" in data

    def test_load_words_from_cache(self):
        """Test loading words from local cache file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "frequent_words.json")
            manager = FrequentWordsManager(cache_file)

            # Create cache file with test data using future date
            from datetime import datetime, timedelta

            future_date = (datetime.now() + timedelta(days=1)).isoformat()
            test_data = {
                "words": ["the", "be", "to", "of", "and"],
                "last_updated": future_date,
            }
            with open(cache_file, "w") as f:
                json.dump(test_data, f)

            words = manager.load_words_from_cache()
            assert words == ["the", "be", "to", "of", "and"]

    def test_load_words_from_cache_file_not_exists(self):
        """Test loading words when cache file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "frequent_words.json")
            manager = FrequentWordsManager(cache_file)

            words = manager.load_words_from_cache()
            assert words is None

    def test_get_frequent_words_with_cache(self):
        """Test getting frequent words using cached data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "frequent_words.json")
            manager = FrequentWordsManager(cache_file)

            # Create cache file with test data using future date
            from datetime import datetime, timedelta

            future_date = (datetime.now() + timedelta(days=1)).isoformat()
            test_data = {
                "words": ["the", "be", "to", "of", "and"],
                "last_updated": future_date,
            }
            with open(cache_file, "w") as f:
                json.dump(test_data, f)

            # Mock the download method to prevent real downloads
            with patch.object(manager, "download_frequent_words") as mock_download:
                words = manager.get_frequent_words()
                assert words == ["the", "be", "to", "of", "and"]
                # Should not call download since cache is valid
                mock_download.assert_not_called()

    def test_get_frequent_words_without_cache(self):
        """Test getting frequent words when cache doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "frequent_words.json")
            manager = FrequentWordsManager(cache_file)

            # Mock the download and save operations
            with (
                patch.object(manager, "download_frequent_words") as mock_download,
                patch.object(manager, "save_words_to_cache") as mock_save,
            ):

                mock_download.return_value = ["the", "be", "to", "of", "and"]

                words = manager.get_frequent_words()

                assert words == ["the", "be", "to", "of", "and"]
                mock_download.assert_called_once()
                mock_save.assert_called_once_with(["the", "be", "to", "of", "and"])

    def test_filter_frequent_words(self):
        """Test filtering out frequent words from a word list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "frequent_words.json")
            manager = FrequentWordsManager(cache_file)

            # Set up frequent words
            frequent_words = ["the", "be", "to", "of", "and", "a", "in"]
            manager._frequent_words = set(frequent_words)

            # Test word list with some frequent words
            test_words = ["the", "serendipity", "be", "ephemeral", "to", "ubiquitous"]

            filtered_words = manager.filter_frequent_words(test_words)

            assert len(filtered_words) == 3
            assert "serendipity" in filtered_words
            assert "ephemeral" in filtered_words
            assert "ubiquitous" in filtered_words
            assert "the" not in filtered_words
            assert "be" not in filtered_words
            assert "to" not in filtered_words

    def test_filter_frequent_words_case_insensitive(self):
        """Test that filtering is case insensitive."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "frequent_words.json")
            manager = FrequentWordsManager(cache_file)

            # Set up frequent words
            frequent_words = ["the", "be", "to", "of", "and"]
            manager._frequent_words = set(frequent_words)

            # Test word list with mixed case
            test_words = ["The", "SERENDIPITY", "BE", "ephemeral", "To"]

            filtered_words = manager.filter_frequent_words(test_words)

            assert len(filtered_words) == 2
            assert "SERENDIPITY" in filtered_words
            assert "ephemeral" in filtered_words
            assert "The" not in filtered_words
            assert "BE" not in filtered_words
            assert "To" not in filtered_words

    def test_cache_expiry(self):
        """Test that cache expires after a certain time."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "frequent_words.json")
            manager = FrequentWordsManager(cache_file)

            # Create cache file with old timestamp
            test_data = {
                "words": ["the", "be", "to", "of", "and"],
                "last_updated": "2020-01-15T10:30:00",  # Old date
            }
            with open(cache_file, "w") as f:
                json.dump(test_data, f)

            # Mock the download and save operations
            with (
                patch.object(manager, "download_frequent_words") as mock_download,
                patch.object(manager, "save_words_to_cache") as mock_save,
            ):

                mock_download.return_value = [
                    "the",
                    "be",
                    "to",
                    "of",
                    "and",
                    "new",
                    "words",
                ]

                words = manager.get_frequent_words()

                # Should download new words due to cache expiry
                assert words == ["the", "be", "to", "of", "and", "new", "words"]
                mock_download.assert_called_once()
                mock_save.assert_called_once()
