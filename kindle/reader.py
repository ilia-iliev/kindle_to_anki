import os
import sqlite3
import random
from datetime import datetime

from platformdirs import user_data_dir

from frequent_words import FrequentWordsManager


DEFAULT_LAST_ACCESS_FILE = os.path.join(
    user_data_dir("kindle-to-anki"), "last_access.txt"
)


class LastAccessManager:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def read(self) -> str | None:
        if not os.path.exists(self.file_path):
            return None
        content = open(self.file_path).read().strip()
        return content or None

    def write(self, date: str) -> None:
        parent = os.path.dirname(self.file_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self.file_path, "w") as f:
            f.write(date)


class KindleReader:
    def __init__(self, kindle_path: str, last_access_file: str | None = None):
        last_access_file = last_access_file or DEFAULT_LAST_ACCESS_FILE
        self.kindle_path = kindle_path
        self.last_access_manager = LastAccessManager(last_access_file)
        self.database_path = os.path.join(
            kindle_path, "system", "vocabulary", "vocab.db"
        )
        self.frequent_words_manager = FrequentWordsManager()

    def _read_kindle_database(self) -> list[dict[str, str]]:
        if not os.path.exists(self.database_path):
            raise FileNotFoundError(
                f"Kindle database not found at {self.database_path}"
            )

        with sqlite3.connect(self.database_path) as conn:
            rows = conn.execute(
                """
                SELECT word, stem, timestamp
                FROM WORDS
                WHERE word IS NOT NULL AND timestamp > 0
                ORDER BY timestamp DESC
                """
            ).fetchall()

        return [
            {
                "word": stem.strip() if stem and stem.strip() else word,
                "timestamp": datetime.fromtimestamp(timestamp / 1000).isoformat(),
            }
            for word, stem, timestamp in rows
            if word and timestamp
        ]

    def get_words_since_last_access(self) -> list[str]:
        all_words = self._read_kindle_database()
        last_access = self.last_access_manager.read()

        if last_access is None:
            words = [item["word"] for item in all_words]
        else:
            words = [
                item["word"] for item in all_words if item["timestamp"] > last_access
            ]

        filtered = self._filter_and_deduplicate(words)
        self.last_access_manager.write(datetime.now().isoformat())
        return filtered

    def get_random_test_words(self, count: int = 10) -> list[str]:
        all_words = self._read_kindle_database()
        filtered = self._filter_and_deduplicate([item["word"] for item in all_words])

        if count >= len(filtered):
            return filtered
        return random.sample(filtered, count)

    def _filter_and_deduplicate(self, words: list[str]) -> list[str]:
        filtered = self.frequent_words_manager.filter_frequent_words(words)
        seen: set[str] = set()
        unique_words = []
        for word in filtered:
            key = word.casefold()
            if key not in seen:
                seen.add(key)
                unique_words.append(word)
        return unique_words
