import pytest
import tempfile
import os
import csv
from unittest.mock import Mock, patch, MagicMock
from kindle_detector import KindleDetector
from kindle_reader import KindleReader
from anki_importer import CSVExporter


class TestIntegration:
    """Integration tests for the complete Kindle to Anki workflow."""

    def test_complete_workflow_with_test_mode(self):
        """Test the complete workflow from Kindle detection to CSV export in test mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock Kindle detector
            with patch("kindle_detector.KindleDetector.detect_kindle") as mock_detect:
                mock_detector = Mock()
                mock_detector.mount_path = "/mock/kindle/path"
                mock_detect.return_value = mock_detector

                # Mock Kindle reader
                with patch(
                    "kindle_reader.KindleReader.get_random_test_words"
                ) as mock_get_words:
                    mock_get_words.return_value = [
                        "testword1",
                        "testword2",
                        "testword3",
                    ]

                    # Mock frequent words manager
                    with patch(
                        "frequent_words.FrequentWordsManager.get_frequent_words"
                    ) as mock_frequent:
                        mock_frequent.return_value = {"the", "and", "or"}

                        # Mock Anki reader
                        with patch(
                            "anki_reader.AnkiReader.get_all_words_from_anki"
                        ) as mock_anki:
                            mock_anki.return_value = {"existingword"}

                            # Test the complete workflow
                            detector = KindleDetector()
                            detector.detect_kindle()

                            reader = KindleReader(detector.mount_path)
                            words = reader.get_random_test_words(3)

                            # Test CSV export
                            exporter = CSVExporter(
                                output_dir=temp_dir, use_dictionary=False
                            )
                            csv_path = exporter.export_words_to_csv(words)

                            # Verify results
                            assert len(words) == 3
                            assert "testword1" in words
                            assert "testword2" in words
                            assert "testword3" in words

                            # Verify CSV file was created
                            assert os.path.exists(csv_path)
                            assert csv_path.endswith("words.csv")

                            # Check CSV content
                            with open(
                                csv_path, "r", newline="", encoding="utf-8"
                            ) as file:
                                reader = csv.reader(file, delimiter=";")
                                rows = list(reader)

                                # Should have 3 word rows
                                assert len(rows) == 3
                                assert rows[0] == [
                                    "testword1",
                                    "Definition of testword1",
                                ]
                                assert rows[1] == [
                                    "testword2",
                                    "Definition of testword2",
                                ]
                                assert rows[2] == [
                                    "testword3",
                                    "Definition of testword3",
                                ]

    def test_workflow_with_empty_word_list(self):
        """Test the workflow when no words are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock Kindle detector
            with patch("kindle_detector.KindleDetector.detect_kindle") as mock_detect:
                mock_detector = Mock()
                mock_detector.mount_path = "/mock/kindle/path"
                mock_detect.return_value = mock_detector

                # Mock Kindle reader to return empty list
                with patch(
                    "kindle_reader.KindleReader.get_random_test_words"
                ) as mock_get_words:
                    mock_get_words.return_value = []

                    # Mock frequent words manager
                    with patch(
                        "frequent_words.FrequentWordsManager.get_frequent_words"
                    ) as mock_frequent:
                        mock_frequent.return_value = {"the", "and", "or"}

                        # Mock Anki reader
                        with patch(
                            "anki_reader.AnkiReader.get_all_words_from_anki"
                        ) as mock_anki:
                            mock_anki.return_value = {"existingword"}

                            # Test the complete workflow
                            detector = KindleDetector()
                            detector.detect_kindle()

                            reader = KindleReader(detector.mount_path)
                            words = reader.get_random_test_words(3)

                            # Test CSV export with empty list
                            exporter = CSVExporter(
                                output_dir=temp_dir, use_dictionary=False
                            )
                            csv_path = exporter.export_words_to_csv(words)

                            # Verify results
                            assert len(words) == 0

                            # Verify CSV file was created with only header
                            assert os.path.exists(csv_path)

                            with open(
                                csv_path, "r", newline="", encoding="utf-8"
                            ) as file:
                                reader = csv.reader(file, delimiter=";")
                                rows = list(reader)

                                assert len(rows) == 0

    def test_workflow_with_custom_deck_name(self):
        """Test the workflow with a custom deck name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock Kindle detector
            with patch("kindle_detector.KindleDetector.detect_kindle") as mock_detect:
                mock_detector = Mock()
                mock_detector.mount_path = "/mock/kindle/path"
                mock_detect.return_value = mock_detector

                # Mock Kindle reader
                with patch(
                    "kindle_reader.KindleReader.get_random_test_words"
                ) as mock_get_words:
                    mock_get_words.return_value = ["word1", "word2"]

                    # Mock frequent words manager
                    with patch(
                        "frequent_words.FrequentWordsManager.get_frequent_words"
                    ) as mock_frequent:
                        mock_frequent.return_value = {"the", "and", "or"}

                        # Mock Anki reader
                        with patch(
                            "anki_reader.AnkiReader.get_all_words_from_anki"
                        ) as mock_anki:
                            mock_anki.return_value = {"existingword"}

                            # Test the complete workflow
                            detector = KindleDetector()
                            detector.detect_kindle()

                            reader = KindleReader(detector.mount_path)
                            words = reader.get_random_test_words(2)

                            # Test CSV export
                            exporter = CSVExporter(
                                output_dir=temp_dir, use_dictionary=False
                            )
                            csv_path = exporter.export_words_to_csv(words)

                            # Verify results
                            assert len(words) == 2

                            # Verify CSV file was created
                            assert os.path.exists(csv_path)
                            assert csv_path.endswith("words.csv")

                            # Verify CSV content
                            with open(
                                csv_path, "r", newline="", encoding="utf-8"
                            ) as file:
                                reader = csv.reader(file, delimiter=";")
                                rows = list(reader)

                                assert len(rows) == 2
                                assert rows[0] == ["word1", "Definition of word1"]
                                assert rows[1] == ["word2", "Definition of word2"]
