import os
from typing import Set, List


class AnkiAccessError(Exception):
    """Exception raised when Anki database cannot be accessed."""

    pass


class AnkiReader:
    """Simple stub for Anki reader that doesn't filter words (no Anki dependency)."""

    def __init__(self, base_path: str | None = None, profile_name: str = "default"):
        """
        Initialize the Anki reader stub.

        Args:
            base_path: Path to Anki base directory (ignored in stub).
            profile_name: Name of the Anki profile to use (ignored in stub).
        """
        # Stub implementation - no actual Anki functionality
        pass

    def verify_test_list_exists(self) -> bool:
        """
        Verify that the test list with 'testword' exists.

        Returns:
            Always returns False since this is a stub.
        """
        return False

    def get_all_words_from_anki(self) -> Set[str]:
        """
        Get all words from all Anki decks.

        Returns:
            Empty set since this is a stub.
        """
        return set()

    def filter_words_against_anki(self, words: List[str]) -> List[str]:
        """
        Filter out words that already exist in Anki.

        Args:
            words: List of words to filter.

        Returns:
            List of words (no filtering applied in stub).
        """
        # Stub implementation - return all words as-is
        return words
