import os
import csv
import re
from typing import List, Optional
from dictionary_service import DictionaryService, DictionaryServiceError


class CSVExportError(Exception):
    """Exception raised when CSV export operations fail."""

    pass


class CSVExporter:
    """Handles exporting words to CSV format."""

    def __init__(self, output_dir: str | None = None, use_dictionary: bool = True):
        """
        Initialize the CSV exporter.

        Args:
            output_dir: Directory to save CSV files. Defaults to current working directory.
            use_dictionary: Whether to fetch real definitions from dictionary API.
        """
        self.output_dir = output_dir or os.getcwd()
        self.use_dictionary = use_dictionary
        self.dictionary_service = DictionaryService() if use_dictionary else None

    def export_words_to_csv(self, words: List[str]) -> str:
        """
        Export words to a CSV file.

        Args:
            words: List of words to export.

        Returns:
            Path to the created CSV file.

        Raises:
            ValueError: If words input is invalid.
            CSVExportError: If CSV file creation fails.
        """
        self._validate_words(words)

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        csv_path = self._get_csv_path()

        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, delimiter=";")

                # Write words
                for word in words:
                    cleaned_word = self._clean_word_for_csv(word)
                    definition = self._get_definition(cleaned_word)
                    writer.writerow([cleaned_word, definition])

        except (OSError, IOError) as e:
            raise CSVExportError(f"Failed to create CSV file: {e}")

        return csv_path

    def _get_csv_path(self) -> str:
        """
        Get the path for the CSV file.

        Returns:
            Path to the CSV file.
        """
        filename = "words.csv"
        return os.path.join(self.output_dir, filename)

    def _validate_words(self, words: List[str]) -> None:
        """
        Validate the words input.

        Args:
            words: List of words to validate.

        Raises:
            ValueError: If words input is invalid.
        """
        if not isinstance(words, list):
            raise ValueError("Words must be a list")

        for word in words:
            if not isinstance(word, str):
                raise ValueError("All words must be strings")
            if not word.strip():
                raise ValueError("Words cannot be empty")

    def _clean_word_for_csv(self, word: str) -> str:
        """
        Clean a word for CSV export.

        Args:
            word: Word to clean.

        Returns:
            Cleaned word.
        """
        # Remove leading/trailing whitespace and normalize internal whitespace
        cleaned = re.sub(r"\s+", " ", word.strip())
        return cleaned

    def _get_definition(self, word: str) -> str:
        """
        Get definition for a word.

        Args:
            word: Word to get definition for.

        Returns:
            Definition of the word, or fallback definition if not found.
        """
        if not self.use_dictionary or not self.dictionary_service:
            # Fallback to dummy definition
            return f"Definition of {word}"

        try:
            definition = self.dictionary_service.get_definition(word)
            if definition:
                return definition
            else:
                return f"Definition not found for {word}"
        except DictionaryServiceError:
            # If dictionary service fails, use fallback
            return f"Definition of {word} (API unavailable)"
