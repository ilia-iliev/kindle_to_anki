import requests
import time
from collections import deque
from urllib.parse import quote

from errors import DictionaryServiceError

CATEGORY_MAP = {
    "verb": "v",
    "noun": "n",
    "adjective": "adj",
    "adverb": "adv",
    "pronoun": "pron",
    "preposition": "prep",
    "conjunction": "conj",
    "interjection": "interj",
}


class RateLimiter:
    def __init__(self, max_per_second: int = 10):
        self.max_per_second = max_per_second
        self.request_times: deque[float] = deque()

    def wait_if_needed(self):
        now = time.time()
        while self.request_times and now - self.request_times[0] >= 1.0:
            self.request_times.popleft()

        if len(self.request_times) >= self.max_per_second:
            sleep_time = 1.0 - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.request_times.append(time.time())


class DictionaryService:
    BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en"

    def __init__(self, max_requests_per_second: int = 10, max_retries: int = 3):
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "KindleToAnki/1.0 (Educational Tool)"}
        )
        self.rate_limiter = RateLimiter(max_requests_per_second)
        self.max_retries = max_retries
        self.timeout = 10

    def get_definition(self, word: str) -> str | None:
        if word is None:
            raise ValueError("Word cannot be None")
        if not word.strip():
            raise ValueError("Word cannot be empty")

        cleaned = word.lower().strip()
        self.rate_limiter.wait_if_needed()

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                url = f"{self.BASE_URL}/{quote(cleaned)}"
                response = self.session.get(url, timeout=self.timeout)

                if response.status_code == 404:
                    return None

                if 400 <= response.status_code < 500 and response.status_code != 429:
                    response.raise_for_status()

                response.raise_for_status()
                return self._extract_definition(response.json())

            except requests.RequestException as e:
                last_exception = e

                if hasattr(e, "response") and e.response is not None:
                    if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                        break

                if attempt == self.max_retries:
                    break

                time.sleep(2**attempt)
                self.rate_limiter.wait_if_needed()

        raise DictionaryServiceError(
            f"Failed to fetch definition for '{word}' after {self.max_retries + 1} attempts: {last_exception}"
        )

    def get_definitions(self, words: list[str]) -> list[str | None]:
        results = []
        for word in words:
            try:
                results.append(self.get_definition(word))
            except DictionaryServiceError:
                results.append(None)
        return results

    def _extract_definition(self, data: list) -> str | None:
        try:
            if not data or not isinstance(data, list):
                return None

            entry = data[0]
            meanings = entry.get("meanings", [])
            if not meanings or not isinstance(meanings, list):
                return None

            all_defs = []
            num = 1
            for meaning in meanings:
                defs = meaning.get("definitions", [])
                category = CATEGORY_MAP.get(
                    meaning.get("partOfSpeech", "").lower(), ""
                )
                for d in defs:
                    text = d.get("definition", "")
                    if not text:
                        continue
                    text = text.replace('"', "").replace("'", "").strip()
                    prefix = f"({category}) " if category else ""
                    all_defs.append(f"{prefix}{num}. {text}")
                    num += 1

            return "\n".join(all_defs) if all_defs else None
        except (KeyError, IndexError, TypeError):
            return None
