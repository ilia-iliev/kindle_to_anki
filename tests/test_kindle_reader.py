import pytest
import tempfile
import os
import sqlite3
from unittest.mock import patch
from kindle.reader import KindleReader, LastAccessManager


class TestLastAccessManager:
    def test_read_returns_none_when_file_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = LastAccessManager(os.path.join(temp_dir, "last_access.txt"))
            assert manager.read() is None

    def test_read_returns_none_when_file_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "last_access.txt")
            open(file_path, "w").close()
            manager = LastAccessManager(file_path)
            assert manager.read() is None

    def test_read_write_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "last_access.txt")
            manager = LastAccessManager(file_path)
            manager.write("2024-01-15T10:30:00")
            assert manager.read() == "2024-01-15T10:30:00"


class TestKindleReader:
    def _create_test_database(self, temp_dir: str) -> str:
        db_path = os.path.join(temp_dir, "vocab.db")
        with sqlite3.connect(db_path) as conn:
            conn.execute(
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
            conn.executemany(
                "INSERT INTO WORDS (id, word, stem, lang, category, timestamp, profileid) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    ("1", "apple", "apple", "en", 0, 1705312200000, "profile1"),
                    ("2", "banana", "banana", "en", 0, 1705315800000, "profile1"),
                    ("3", "cherry", "cherry", "en", 0, 1705319400000, "profile1"),
                ],
            )
        return db_path

    def _make_reader(self, temp_dir: str) -> KindleReader:
        db_path = self._create_test_database(temp_dir)
        last_access_file = os.path.join(temp_dir, "last_access.txt")
        reader = KindleReader("/fake/kindle/path", last_access_file)
        reader.database_path = db_path
        return reader

    def test_get_words_since_last_access(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            reader = self._make_reader(temp_dir)
            with patch.object(
                reader.frequent_words_manager,
                "filter_frequent_words",
                side_effect=lambda w: w,
            ):
                words = reader.get_words_since_last_access()
                assert set(words) == {"apple", "banana", "cherry"}

    def test_get_words_since_last_access_with_date_filter(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            reader = self._make_reader(temp_dir)
            reader.last_access_manager.write("2024-01-15T14:00:00")
            words = reader.get_words_since_last_access()
            assert len(words) == 0

    def test_get_random_test_words(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            reader = self._make_reader(temp_dir)
            with patch.object(
                reader.frequent_words_manager,
                "filter_frequent_words",
                side_effect=lambda w: w,
            ):
                words = reader.get_random_test_words(2)
                assert len(words) == 2
                assert all(w in ["apple", "banana", "cherry"] for w in words)

    def test_read_kindle_database_file_not_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            reader = KindleReader(
                "/fake/kindle/path",
                os.path.join(temp_dir, "last_access.txt"),
            )
            with pytest.raises(FileNotFoundError):
                reader._read_kindle_database()

    def test_updates_last_access_date(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            reader = self._make_reader(temp_dir)
            reader.get_words_since_last_access()
            assert reader.last_access_manager.read() is not None
