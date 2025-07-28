import os
import sqlite3
import random
from datetime import datetime
from typing import List, Dict, Optional
from frequent_words import FrequentWordsManager
from anki_reader import AnkiReader


class LastAccessManager:
    """Manages the last access date stored in a plaintext file."""

    def __init__(self, file_path: str):
        """
        Initialize the last access manager.

        Args:
            file_path: Path to the plaintext file storing the last access date.
        """
        self.file_path = file_path

    def initialize_if_needed(self) -> None:
        """Initialize the file if it doesn't exist."""
        if not os.path.exists(self.file_path):
            # Create empty file
            with open(self.file_path, "w") as f:
                pass

    def read_last_access_date(self) -> Optional[str]:
        """
        Read the last access date from the file.

        Returns:
            The last access date as a string, or None if file is empty.
        """
        self.initialize_if_needed()

        with open(self.file_path, "r") as f:
            content = f.read().strip()

        return content if content else None

    def write_last_access_date(self, date: str) -> None:
        """
        Write the last access date to the file.

        Args:
            date: The date to write (ISO format string).
        """
        self.initialize_if_needed()

        with open(self.file_path, "w") as f:
            f.write(date)


class KindleReader:
    """Reads word lookups from Kindle database."""

    def __init__(self, kindle_path: str, last_access_file: str = "last_access.txt"):
        """
        Initialize the Kindle reader.

        Args:
            kindle_path: Path to the Kindle device.
            last_access_file: Path to the file storing last access date.
        """
        self.kindle_path = kindle_path
        self.last_access_manager = LastAccessManager(last_access_file)
        self.database_path = os.path.join(
            kindle_path, "system", "vocabulary", "vocab.db"
        )
        self.frequent_words_manager = FrequentWordsManager()
        self.anki_reader = AnkiReader(profile_name="ilia")

    def _read_kindle_database(self) -> List[Dict[str, str]]:
        """
        Read the Kindle vocabulary database.

        Returns:
            List of dictionaries containing word and timestamp data.

        Raises:
            FileNotFoundError: If the database file doesn't exist.
        """
        if not os.path.exists(self.database_path):
            raise FileNotFoundError(
                f"Kindle database not found at {self.database_path}"
            )

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            # Query the WORDS table to get all words with timestamps
            cursor.execute(
                """
                SELECT word, timestamp
                FROM WORDS
                WHERE word IS NOT NULL AND timestamp > 0
                ORDER BY timestamp DESC
            """
            )

            results = cursor.fetchall()
            conn.close()

            # Convert Unix timestamps (milliseconds) to ISO format strings
            words_data = []
            for word, timestamp in results:
                if word and timestamp:
                    # Convert milliseconds to seconds, then to datetime
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    iso_timestamp = dt.isoformat()
                    words_data.append({"word": word, "timestamp": iso_timestamp})

            return words_data

        except sqlite3.Error as e:
            raise Exception(f"Error reading Kindle database: {e}")

    def get_words_since_last_access(self) -> List[str]:
        """
        Get words that have been looked up since the last access.

        Returns:
            List of words looked up since last access, with frequent words and Anki words filtered out.
        """
        # Read all words from database
        all_words = self._read_kindle_database()

        # Get last access date
        last_access_date = self.last_access_manager.read_last_access_date()

        if last_access_date is None:
            # First time running, return all words
            words = [item["word"] for item in all_words]
        else:
            # Filter words since last access
            words = []
            for item in all_words:
                if item["timestamp"] > last_access_date:
                    words.append(item["word"])

        # Filter out frequent words
        filtered_words = self.frequent_words_manager.filter_frequent_words(words)

        # Filter out words that already exist in Anki
        final_words = self.anki_reader.filter_words_against_anki(filtered_words)

        # Update last access date to current time
        current_time = datetime.now().isoformat()
        self.last_access_manager.write_last_access_date(current_time)

        return final_words

    def get_random_test_words(self, count: int = 10) -> List[str]:
        """
        Get random words for testing purposes.

        Args:
            count: Number of random words to return.

        Returns:
            List of random words, with frequent words and Anki words filtered out.
        """
        all_words = self._read_kindle_database()
        word_list = [item["word"] for item in all_words]

        # Filter out frequent words first
        filtered_words = self.frequent_words_manager.filter_frequent_words(word_list)

        # Filter out words that already exist in Anki
        final_words = self.anki_reader.filter_words_against_anki(filtered_words)

        # Return random sample, or all words if count is greater than available
        if count >= len(final_words):
            return final_words
        else:
            return random.sample(final_words, count)
