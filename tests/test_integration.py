import tempfile
import os
import csv
from unittest.mock import patch
from csv_exporter import CSVExporter


class TestIntegration:
    def test_export_workflow_with_mocked_dictionary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = CSVExporter(output_dir=temp_dir)
            words = ["testword1", "testword2", "testword3"]

            with patch.object(
                exporter.dictionary_service,
                "get_definition",
                side_effect=lambda w: f"Definition of {w}",
            ):
                csv_path = exporter.export_words_to_csv(words)
                assert os.path.exists(csv_path)

                with open(csv_path, "r", newline="", encoding="utf-8") as f:
                    rows = list(csv.reader(f, delimiter=";"))

                assert len(rows) == 3
                assert rows[0] == ["testword1", "Definition of testword1"]

    def test_export_workflow_with_empty_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = CSVExporter(output_dir=temp_dir)
            csv_path = exporter.export_words_to_csv([])
            assert os.path.exists(csv_path)

            with open(csv_path, "r", newline="", encoding="utf-8") as f:
                assert list(csv.reader(f, delimiter=";")) == []
