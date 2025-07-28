import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Optional


class FrequentWordsManager:
    """Manages downloading and caching of frequent English words."""

    def __init__(
        self, cache_file: str = "frequent_words.json", cache_expiry_days: int = 30
    ):
        """
        Initialize the frequent words manager.

        Args:
            cache_file: Path to the JSON cache file.
            cache_expiry_days: Number of days before cache expires.
        """
        self.cache_file = cache_file
        self.cache_expiry_days = cache_expiry_days
        self._frequent_words = set()

    def download_frequent_words(self) -> List[str]:
        """
        Download the top 1000 most frequent English words from the internet.

        Returns:
            List of frequent words.

        Raises:
            Exception: If download fails.
        """
        try:
            # Use a reliable source for frequent words
            # This URL provides the top 1000 English words
            url = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-usa-no-swears-short.txt"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse the response - each word is on a separate line
            words = []
            for line in response.text.strip().split("\n"):
                word = line.strip().lower()
                if word and len(word) > 1:  # Skip empty lines and single characters
                    words.append(word)

            # Take the top 1000 words
            return words[:1000]

        except requests.RequestException as e:
            raise Exception(f"Failed to download frequent words: {e}")

    def save_words_to_cache(self, words: List[str]) -> None:
        """
        Save words to the local cache file.

        Args:
            words: List of words to save.
        """
        cache_data = {"words": words, "last_updated": datetime.now().isoformat()}

        # Ensure directory exists
        os.makedirs(
            (
                os.path.dirname(self.cache_file)
                if os.path.dirname(self.cache_file)
                else "."
            ),
            exist_ok=True,
        )

        with open(self.cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

    def load_words_from_cache(self) -> Optional[List[str]]:
        """
        Load words from the local cache file.

        Returns:
            List of words if cache exists and is valid, None otherwise.
        """
        if not os.path.exists(self.cache_file):
            return None

        try:
            with open(self.cache_file, "r") as f:
                cache_data = json.load(f)

            # Check if cache has expired
            last_updated = datetime.fromisoformat(cache_data["last_updated"])
            expiry_date = last_updated + timedelta(days=self.cache_expiry_days)

            if datetime.now() > expiry_date:
                return None  # Cache expired

            return cache_data["words"]

        except (json.JSONDecodeError, KeyError, ValueError):
            return None  # Invalid cache file

    def get_frequent_words(self) -> List[str]:
        """
        Get frequent words, either from cache or by downloading.

        Returns:
            List of frequent words.
        """
        # Try to load from cache first
        cached_words = self.load_words_from_cache()

        if cached_words is not None:
            self._frequent_words = set(cached_words)
            return cached_words

        # Download if cache doesn't exist or is expired
        words = self.download_frequent_words()
        self.save_words_to_cache(words)
        self._frequent_words = set(words)
        return words

    def filter_frequent_words(self, words: List[str]) -> List[str]:
        """
        Filter out frequent words from a list of words.

        Args:
            words: List of words to filter.

        Returns:
            List of words with frequent words removed.
        """
        # Ensure we have frequent words loaded
        if not self._frequent_words:
            self.get_frequent_words()

        # Filter out frequent words (case insensitive)
        filtered_words = []
        for word in words:
            if word.lower() not in self._frequent_words:
                filtered_words.append(word)

        return filtered_words

    def is_frequent_word(self, word: str) -> bool:
        """
        Check if a word is in the frequent words list.

        Args:
            word: Word to check.

        Returns:
            True if the word is frequent, False otherwise.
        """
        # Ensure we have frequent words loaded
        if not self._frequent_words:
            self.get_frequent_words()

        return word.lower() in self._frequent_words
