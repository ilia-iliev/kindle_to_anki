import pytest
import tempfile
import os
import csv
from unittest.mock import Mock, patch, mock_open
from anki_importer import CSVExporter, CSVExportError


class TestCSVExporter:
    """Test cases for CSVExporter class."""

    def test_init_with_default_output_dir(self):
        """Test CSVExporter initialization with default output directory."""
        exporter = CSVExporter()
        assert exporter.output_dir == os.getcwd()

    def test_init_with_custom_output_dir(self):
        """Test CSVExporter initialization with custom output directory."""
        exporter = CSVExporter(output_dir="/custom/path")
        assert exporter.output_dir == "/custom/path"

    def test_export_words_to_csv_success(self):
        """Test successful CSV export of words."""
        words = ["hello", "world", "test"]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Disable dictionary service for testing
            exporter = CSVExporter(output_dir=temp_dir, use_dictionary=False)
            csv_path = exporter.export_words_to_csv(words)

            # Check file was created
            assert os.path.exists(csv_path)
            assert csv_path.endswith("words.csv")

            # Check CSV content
            with open(csv_path, "r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file, delimiter=";")
                rows = list(reader)

                # Should have 3 word rows
                assert len(rows) == 3
                assert rows[0] == ["hello", "Definition of hello"]
                assert rows[1] == ["world", "Definition of world"]
                assert rows[2] == ["test", "Definition of test"]

    def test_export_words_to_csv_empty_list(self):
        """Test CSV export with empty word list."""
        words = []

        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = CSVExporter(output_dir=temp_dir)
            csv_path = exporter.export_words_to_csv(words)

            # Check file was created with only header
            assert os.path.exists(csv_path)

            with open(csv_path, "r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file, delimiter=";")
                rows = list(reader)

                assert len(rows) == 0

    def test_export_words_to_csv_with_special_characters(self):
        """Test CSV export with words containing special characters."""
        words = ["café", "naïve", "résumé"]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Disable dictionary service for testing
            exporter = CSVExporter(output_dir=temp_dir, use_dictionary=False)
            csv_path = exporter.export_words_to_csv(words)

            with open(csv_path, "r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file, delimiter=";")
                rows = list(reader)

                assert rows[1] == ["café", "Definition of café"]
                assert rows[2] == ["naïve", "Definition of naïve"]
                assert rows[3] == ["résumé", "Definition of résumé"]

    def test_export_words_to_csv_directory_not_exists(self):
        """Test CSV export when output directory doesn't exist."""
        words = ["hello", "world"]

        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_dir = os.path.join(temp_dir, "non_existent")
            exporter = CSVExporter(output_dir=non_existent_dir)

            # Should create directory and export successfully
            csv_path = exporter.export_words_to_csv(words)
            assert os.path.exists(csv_path)

    def test_export_words_to_csv_permission_error(self):
        """Test CSV export when there's a permission error."""
        words = ["hello", "world"]

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            exporter = CSVExporter()
            with pytest.raises(CSVExportError, match="Failed to create CSV file"):
                exporter.export_words_to_csv(words)

    def test_export_words_to_csv_io_error(self):
        """Test CSV export when there's an IO error."""
        words = ["hello", "world"]

        with patch("builtins.open", side_effect=OSError("Disk full")):
            exporter = CSVExporter()
            with pytest.raises(CSVExportError, match="Failed to create CSV file"):
                exporter.export_words_to_csv(words)

    def test_get_csv_path(self):
        """Test getting CSV file path."""
        exporter = CSVExporter(output_dir="/test/path")
        csv_path = exporter._get_csv_path()
        assert csv_path == "/test/path/words.csv"

    def test_validate_words_input(self):
        """Test validation of words input."""
        exporter = CSVExporter()

        # Valid input
        valid_words = ["hello", "world", "test"]
        assert exporter._validate_words(valid_words) is None

        # Invalid input - not a list
        with pytest.raises(ValueError, match="Words must be a list"):
            exporter._validate_words("not a list")

        # Invalid input - contains non-strings
        with pytest.raises(ValueError, match="All words must be strings"):
            exporter._validate_words(["hello", 123, "world"])

        # Invalid input - contains empty strings
        with pytest.raises(ValueError, match="Words cannot be empty"):
            exporter._validate_words(["hello", "", "world"])

    def test_clean_word_for_csv(self):
        """Test word cleaning for CSV export."""
        exporter = CSVExporter()
        assert exporter._clean_word_for_csv("  hello  ") == "hello"
        assert exporter._clean_word_for_csv("hello world") == "hello world"
        assert exporter._clean_word_for_csv("hello\nworld") == "hello world"

    def test_export_words_to_csv_with_dictionary_service(self):
        """Test CSV export with dictionary service enabled."""
        words = ["hello", "world"]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Enable dictionary service
            exporter = CSVExporter(output_dir=temp_dir, use_dictionary=True)
            csv_path = exporter.export_words_to_csv(words)

            # Check file was created
            assert os.path.exists(csv_path)

            # Check CSV content
            with open(csv_path, "r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file, delimiter=";")
                rows = list(reader)

                # Should have 2 word rows
                assert len(rows) == 2

                # Check that we got real definitions (not dummy ones)
                assert rows[0][0] == "hello"
                assert rows[0][1] != "Definition of hello"
                assert len(rows[0][1]) > 0

                assert rows[1][0] == "world"
                assert rows[1][1] != "Definition of world"
                assert len(rows[1][1]) > 0
