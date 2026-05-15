import os
import csv
import re
from dictionary_service import DictionaryService
from errors import CSVExportError


class CSVExporter:
    def __init__(self, output_dir: str | None = None):
        self.output_dir = output_dir or os.getcwd()
        self.dictionary_service = DictionaryService()

    def export_words_to_csv(self, words: list[str]) -> str:
        if not isinstance(words, list):
            raise ValueError("Words must be a list")
        for word in words:
            if not isinstance(word, str) or not word.strip():
                raise ValueError("All words must be non-empty strings")

        os.makedirs(self.output_dir, exist_ok=True)
        csv_path = os.path.join(self.output_dir, "words.csv")

        cleaned = [re.sub(r"\s+", " ", w.strip()) for w in words]
        definitions = self.dictionary_service.get_definitions(cleaned)

        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, delimiter=";")
                for word, definition in zip(cleaned, definitions):
                    if definition and definition.strip():
                        writer.writerow([word, definition])
        except (OSError, IOError) as e:
            raise CSVExportError(f"Failed to create CSV file: {e}")

        return csv_path
