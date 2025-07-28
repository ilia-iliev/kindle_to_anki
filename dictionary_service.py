import requests
import time
from typing import List, Optional, Deque
from urllib.parse import quote
from collections import deque


class DictionaryServiceError(Exception):
    """Exception raised when dictionary service operations fail."""

    pass


class RateLimiter:
    """Rate limiter that enforces maximum requests per second."""

    def __init__(self, max_requests_per_second: int = 10):
        """Initialize rate limiter.

        Args:
            max_requests_per_second: Maximum number of requests allowed per second.
        """
        self.max_requests_per_second = max_requests_per_second
        self.request_times: Deque[float] = deque()

    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()

        # Remove requests older than 1 second
        while self.request_times and current_time - self.request_times[0] >= 1.0:
            self.request_times.popleft()

        # If we've made max requests in the last second, wait
        if len(self.request_times) >= self.max_requests_per_second:
            sleep_time = 1.0 - (current_time - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)

        # Record this request
        self.request_times.append(time.time())


class DictionaryService:
    """Service for fetching word definitions from Cambridge Dictionary."""

    def __init__(self, max_requests_per_second: int = 10, max_retries: int = 3):
        """Initialize the dictionary service.

        Args:
            max_requests_per_second: Maximum requests per second (default: 10)
            max_retries: Maximum number of retries for failed requests (default: 3)
        """
        self.base_url = "https://api.dictionaryapi.dev/api/v2/entries/en"
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(max_requests_per_second)
        self.max_retries = max_retries

        # Set a reasonable timeout and user agent
        self.session.timeout = 10
        self.session.headers.update(
            {"User-Agent": "KindleToAnki/1.0 (Educational Tool)"}
        )

    def get_definition(self, word: str) -> Optional[str]:
        """
        Get the definition of a word from Cambridge Dictionary.

        Args:
            word: The word to look up.

        Returns:
            The definition of the word, or None if not found.

        Raises:
            ValueError: If word is None or empty.
            DictionaryServiceError: If the API request fails after all retries.
        """
        if word is None:
            raise ValueError("Word cannot be None")

        if not word.strip():
            raise ValueError("Word cannot be empty")

        cleaned_word = self._clean_word(word)

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                # Use Free Dictionary API
                url = f"{self.base_url}/{quote(cleaned_word)}"
                response = self.session.get(url)

                # Handle 404 (word not found) gracefully - don't retry
                if response.status_code == 404:
                    return None

                # Don't retry on client errors (4xx) except 429 (rate limit)
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    response.raise_for_status()

                response.raise_for_status()

                data = response.json()

                # Extract definition from the response
                definition = self._extract_definition(data)
                return definition

            except requests.RequestException as e:
                last_exception = e

                # Don't retry on client errors (4xx) except 429 (rate limit)
                if hasattr(e, "response") and e.response is not None:
                    if (
                        400 <= e.response.status_code < 500
                        and e.response.status_code != 429
                    ):
                        # Break out of retry loop for client errors
                        break

                # If this is the last attempt, raise the exception
                if attempt == self.max_retries:
                    break

                # Calculate exponential backoff delay: 1s, 2s, 4s, etc.
                delay = 2**attempt
                time.sleep(delay)

                # Apply rate limiting before retry
                self.rate_limiter.wait_if_needed()

        # If we get here, all retries failed
        raise DictionaryServiceError(
            f"Failed to fetch definition for '{word}' after {self.max_retries + 1} attempts: {last_exception}"
        )

    def get_definitions(self, words: List[str]) -> List[Optional[str]]:
        """
        Get definitions for multiple words.

        Args:
            words: List of words to look up.

        Returns:
            List of definitions, with None for words not found.

        Raises:
            ValueError: If words input is invalid.
        """
        if not isinstance(words, list):
            raise ValueError("Words must be a list")

        definitions = []
        for word in words:
            try:
                definition = self.get_definition(word)
                definitions.append(definition)
            except DictionaryServiceError:
                # If we can't fetch a definition, return None
                definitions.append(None)

        return definitions

    def _clean_word(self, word: str) -> str:
        """
        Clean a word for API lookup.

        Args:
            word: Word to clean.

        Returns:
            Cleaned word.
        """
        # Convert to lowercase and remove extra whitespace
        cleaned = word.lower().strip()
        return cleaned

    def _extract_definition(self, data: list) -> Optional[str]:
        """
        Extract definition from Free Dictionary API response.

        Args:
            data: Response data from the API.

        Returns:
            Extracted definition or None if not found.
        """
        try:
            # Free Dictionary API returns a list of entries
            if not data or not isinstance(data, list):
                return None

            # Get the first entry
            entry = data[0]

            # Look for meanings in the entry
            if "meanings" in entry and entry["meanings"]:
                meaning = entry["meanings"][0]  # Get first meaning

                # Look for definitions in the meaning
                if "definitions" in meaning and meaning["definitions"]:
                    definition_obj = meaning["definitions"][0]  # Get first definition

                    if "definition" in definition_obj:
                        return definition_obj["definition"]

            return None

        except (KeyError, IndexError, TypeError):
            return None
