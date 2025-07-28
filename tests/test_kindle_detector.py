import pytest
from unittest.mock import patch, MagicMock
from kindle_detector import (
    KindleDetector,
    KindleNotAttachedError,
    KindleNotReadableError,
)
import os


class TestKindleDetector:
    """Test cases for KindleDetector class."""

    def test_detect_kindle_when_attached_and_readable(self):
        """Test successful detection when Kindle is attached and readable."""
        with (
            patch("kindle_detector.os.path.exists") as mock_exists,
            patch("kindle_detector.os.access") as mock_access,
        ):

            # Mock the path checking behavior
            def exists_side_effect(path):
                return (
                    path == "/media/ilia/Kindle"
                )  # Simulate finding Kindle at this path

            def access_side_effect(path, mode):
                return path == "/media/ilia/Kindle" and mode == os.R_OK

            mock_exists.side_effect = exists_side_effect
            mock_access.side_effect = access_side_effect

            detector = KindleDetector()
            result = detector.detect_kindle()

            assert result is True
            assert mock_exists.call_count >= 1
            assert mock_access.call_count >= 1

    def test_detect_kindle_when_not_attached(self):
        """Test detection when Kindle is not attached."""
        with patch("kindle_detector.os.path.exists") as mock_exists:
            mock_exists.return_value = False

            detector = KindleDetector()

            with pytest.raises(KindleNotAttachedError) as exc_info:
                detector.detect_kindle()

            assert "Kindle is not attached" in str(exc_info.value)
            assert mock_exists.call_count >= 1

    def test_detect_kindle_when_attached_but_not_readable(self):
        """Test detection when Kindle is attached but not readable."""
        with (
            patch("kindle_detector.os.path.exists") as mock_exists,
            patch("kindle_detector.os.access") as mock_access,
        ):

            # Mock finding a path but not having read access
            def exists_side_effect(path):
                return path == "/media/ilia/Kindle"

            def access_side_effect(path, mode):
                return False  # No read access

            mock_exists.side_effect = exists_side_effect
            mock_access.side_effect = access_side_effect

            # Use a custom mount path to avoid conflicts with real device
            detector = KindleDetector(mount_path="/media/ilia/Kindle")

            with pytest.raises(KindleNotReadableError) as exc_info:
                detector.detect_kindle()

            assert "Kindle is attached but not readable" in str(exc_info.value)
            assert mock_exists.call_count >= 1
            assert mock_access.call_count >= 1

    def test_get_helpful_message_when_not_attached(self):
        """Test getting helpful message when Kindle is not attached."""
        detector = KindleDetector()
        message = detector.get_helpful_message(KindleNotAttachedError())

        assert "Please connect your Kindle device" in message
        assert "USB cable" in message

    def test_get_helpful_message_when_not_readable(self):
        """Test getting helpful message when Kindle is not readable."""
        detector = KindleDetector()
        message = detector.get_helpful_message(KindleNotReadableError())

        assert "Kindle is connected but not accessible" in message
        assert "permissions" in message

    def test_detect_kindle_with_custom_mount_path(self):
        """Test detection with custom mount path."""
        custom_path = "/custom/kindle/path"

        with (
            patch("kindle_detector.os.path.exists") as mock_exists,
            patch("kindle_detector.os.access") as mock_access,
        ):

            mock_exists.return_value = True
            mock_access.return_value = True

            detector = KindleDetector(mount_path=custom_path)
            result = detector.detect_kindle()

            assert result is True
            mock_exists.assert_called_with(custom_path)
            mock_access.assert_called_with(custom_path, os.R_OK)

    def test_find_kindle_mount_paths(self):
        """Test finding all possible Kindle mount paths."""
        with patch("kindle_detector.os.path.exists") as mock_exists:
            # Mock finding some paths
            def exists_side_effect(path):
                return path in ["/media/Kindle", "/media/ilia/Kindle"]

            mock_exists.side_effect = exists_side_effect

            detector = KindleDetector()
            found_paths = detector.find_kindle_mount_paths()

            assert "/media/Kindle" in found_paths
            assert "/media/ilia/Kindle" in found_paths
