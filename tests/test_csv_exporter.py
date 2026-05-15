import pytest
import tempfile
import os
import csv
from unittest.mock import patch
from csv_exporter import CSVExporter
from errors import CSVExportError


class TestCSVExporter:
    def test_init_defaults_to_cwd(self):
        exporter = CSVExporter()
        assert exporter.output_dir == os.getcwd()

    def test_init_with_custom_output_dir(self):
        exporter = CSVExporter(output_dir="/custom/path")
        assert exporter.output_dir == "/custom/path"

    def test_export_with_mocked_definitions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = CSVExporter(output_dir=temp_dir)
            with patch.object(
                exporter.dictionary_service,
                "get_definition",
                side_effect=lambda w: f"def of {w}",
            ):
                csv_path = exporter.export_words_to_csv(["hello", "world"])
                assert os.path.exists(csv_path)

                with open(csv_path, "r", newline="", encoding="utf-8") as f:
                    rows = list(csv.reader(f, delimiter=";"))

                assert len(rows) == 2
                assert rows[0] == ["hello", "def of hello"]
                assert rows[1] == ["world", "def of world"]

    def test_export_filters_out_words_without_definitions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = CSVExporter(output_dir=temp_dir)
            with patch.object(
                exporter.dictionary_service,
                "get_definition",
                side_effect=lambda w: "a def" if w == "hello" else None,
            ):
                csv_path = exporter.export_words_to_csv(["hello", "unknown"])

                with open(csv_path, "r", newline="", encoding="utf-8") as f:
                    rows = list(csv.reader(f, delimiter=";"))

                assert len(rows) == 1
                assert rows[0][0] == "hello"

    def test_export_empty_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = CSVExporter(output_dir=temp_dir)
            csv_path = exporter.export_words_to_csv([])
            assert os.path.exists(csv_path)

            with open(csv_path, "r", newline="", encoding="utf-8") as f:
                assert list(csv.reader(f, delimiter=";")) == []

    def test_export_creates_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            nested = os.path.join(temp_dir, "sub", "dir")
            exporter = CSVExporter(output_dir=nested)
            csv_path = exporter.export_words_to_csv([])
            assert os.path.exists(csv_path)

    def test_export_permission_error(self):
        exporter = CSVExporter()
        with (
            patch.object(
                exporter.dictionary_service, "get_definitions", return_value=["a def"]
            ),
            patch("builtins.open", side_effect=PermissionError("denied")),
        ):
            with pytest.raises(CSVExportError):
                exporter.export_words_to_csv(["hello"])

    def test_validates_input(self):
        exporter = CSVExporter()
        with pytest.raises(ValueError):
            exporter.export_words_to_csv("not a list")
        with pytest.raises(ValueError):
            exporter.export_words_to_csv([123])
        with pytest.raises(ValueError):
            exporter.export_words_to_csv(["hello", ""])

    def test_export_with_real_dictionary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = CSVExporter(output_dir=temp_dir)
            csv_path = exporter.export_words_to_csv(["hello"])
            assert os.path.exists(csv_path)

            with open(csv_path, "r", newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f, delimiter=";"))

            assert len(rows) == 1
            assert rows[0][0] == "hello"
            assert len(rows[0][1]) > 0
