import pytest
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock
from kindle_reader import KindleReader, LastAccessManager


class TestLastAccessManager:
    """Test cases for LastAccessManager class."""

    def test_initialize_file_if_not_exists(self):
        """Test initializing the last access file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "last_access.txt")
            manager = LastAccessManager(file_path)

            # File should not exist initially
            assert not os.path.exists(file_path)

            # Initialize should create the file
            manager.initialize_if_needed()
            assert os.path.exists(file_path)

    def test_read_last_access_date(self):
        """Test reading the last access date from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "last_access.txt")
            manager = LastAccessManager(file_path)

            # Create file with a date
            with open(file_path, "w") as f:
                f.write("2024-01-15T10:30:00")

            date = manager.read_last_access_date()
            assert date == "2024-01-15T10:30:00"

    def test_write_last_access_date(self):
        """Test writing the last access date to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "last_access.txt")
            manager = LastAccessManager(file_path)

            test_date = "2024-01-15T10:30:00"
            manager.write_last_access_date(test_date)

            # Read back the date
            with open(file_path, "r") as f:
                content = f.read().strip()

            assert content == test_date

    def test_read_empty_file_returns_none(self):
        """Test reading from empty file returns None."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "last_access.txt")
            manager = LastAccessManager(file_path)

            # Create empty file
            with open(file_path, "w") as f:
                pass

            date = manager.read_last_access_date()
            assert date is None


class TestKindleReader:
    """Test cases for KindleReader class."""

    def _create_test_database(self, temp_dir: str) -> str:
        """Create a test SQLite database with sample data."""
        db_path = os.path.join(temp_dir, "vocab.db")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the WORDS table
        cursor.execute(
            """
            CREATE TABLE WORDS (
                id TEXT PRIMARY KEY NOT NULL,
                word TEXT,
                stem TEXT,
                lang TEXT,
                category INTEGER DEFAULT 0,
                timestamp INTEGER DEFAULT 0,
                profileid TEXT
            )
        """
        )

        # Insert test data with Unix timestamps (milliseconds)
        test_data = [
            (
                "1",
                "apple",
                "apple",
                "en",
                0,
                1705312200000,
                "profile1",
            ),  # 2024-01-15T10:30:00
            (
                "2",
                "banana",
                "banana",
                "en",
                0,
                1705315800000,
                "profile1",
            ),  # 2024-01-15T11:30:00
            (
                "3",
                "cherry",
                "cherry",
                "en",
                0,
                1705319400000,
                "profile1",
            ),  # 2024-01-15T12:30:00
        ]

        cursor.executemany(
            """
            INSERT INTO WORDS (id, word, stem, lang, category, timestamp, profileid)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            test_data,
        )

        conn.commit()
        conn.close()

        return db_path

    def test_get_words_since_last_access(self):
        """Test getting words since last access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test database
            db_path = self._create_test_database(temp_dir)

            # Create KindleReader with test database path
            last_access_file = os.path.join(temp_dir, "last_access.txt")
            reader = KindleReader("/fake/kindle/path", last_access_file)

            # Patch the instance attribute
            reader.database_path = db_path

            # Mock the frequent words manager to not filter anything
            with patch.object(
                reader.frequent_words_manager, "filter_frequent_words"
            ) as mock_filter:
                mock_filter.return_value = ["apple", "banana", "cherry"]

                words = reader.get_words_since_last_access()

                assert len(words) == 3
                assert "apple" in words
                assert "banana" in words
                assert "cherry" in words

    def test_get_words_since_last_access_with_filter(self):
        """Test getting words since last access with date filtering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test database
            db_path = self._create_test_database(temp_dir)

            last_access_file = os.path.join(temp_dir, "last_access.txt")

            # Set last access date to after all test words (so no words should be returned)
            reader = KindleReader("/fake/kindle/path", last_access_file)
            reader.last_access_manager.write_last_access_date("2024-01-15T14:00:00")

            # Patch the instance attribute
            reader.database_path = db_path

            words = reader.get_words_since_last_access()
            # Should return no words since all test words are before 14:00:00
            assert len(words) == 0

    def test_get_random_test_words(self):
        """Test getting random test words."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test database
            db_path = self._create_test_database(temp_dir)

            last_access_file = os.path.join(temp_dir, "last_access.txt")
            reader = KindleReader("/fake/kindle/path", last_access_file)

            # Patch the instance attribute
            reader.database_path = db_path

            # Mock the frequent words manager to not filter anything
            with patch.object(
                reader.frequent_words_manager, "filter_frequent_words"
            ) as mock_filter:
                mock_filter.return_value = ["apple", "banana", "cherry"]

                words = reader.get_random_test_words(2)

                assert len(words) == 2
                # All words should be from the original list
                all_words = ["apple", "banana", "cherry"]
                for word in words:
                    assert word in all_words

    def test_read_kindle_database_file_not_found(self):
        """Test handling when database file is not found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            last_access_file = os.path.join(temp_dir, "last_access.txt")
            reader = KindleReader("/fake/kindle/path", last_access_file)

            with pytest.raises(FileNotFoundError):
                reader._read_kindle_database()

    def test_update_last_access_date(self):
        """Test updating the last access date after reading words."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test database
            db_path = self._create_test_database(temp_dir)

            last_access_file = os.path.join(temp_dir, "last_access.txt")
            reader = KindleReader("/fake/kindle/path", last_access_file)

            # Patch the instance attribute
            reader.database_path = db_path

            reader.get_words_since_last_access()

            # Check that last access date was updated
            last_date = reader.last_access_manager.read_last_access_date()
            assert last_date is not None
