import os
from typing import Optional


class KindleNotAttachedError(Exception):
    """Raised when Kindle device is not attached."""

    pass


class KindleNotReadableError(Exception):
    """Raised when Kindle device is attached but not readable."""

    pass


class KindleDetector:
    """Detects if a Kindle device is attached and readable."""

    def __init__(self, mount_path: Optional[str] = None):
        """
        Initialize the Kindle detector.

        Args:
            mount_path: Custom path to check for Kindle. If None, uses default paths.
        """
        self.mount_path = mount_path or self._get_default_mount_path()

    def _get_default_mount_path(self) -> str:
        """
        Get the default mount path for Kindle devices on Linux.

        Returns:
            Default mount path for Kindle devices.
        """
        # Check all possible Kindle mount paths
        possible_paths = [
            "/media/Kindle",
            "/media/kindle",
            "/media/*/Kindle",
            "/media/*/kindle",
            "/mnt/Kindle",
            "/mnt/kindle",
            "/run/media/*/Kindle",
            "/run/media/*/kindle",
        ]

        # Check each path
        for path in possible_paths:
            if "*" in path:
                # Handle wildcard paths
                import glob

                matches = glob.glob(path)
                for match in matches:
                    if os.path.exists(match) and os.access(match, os.R_OK):
                        return match
            else:
                # Direct path check
                if os.path.exists(path) and os.access(path, os.R_OK):
                    return path

        # If no Kindle found, return the most common path for error messages
        return "/media/Kindle"

    def detect_kindle(self) -> bool:
        """
        Detect if a Kindle device is attached and readable.

        Returns:
            True if Kindle is attached and readable.

        Raises:
            KindleNotAttachedError: If Kindle is not attached.
            KindleNotReadableError: If Kindle is attached but not readable.
        """
        if not os.path.exists(self.mount_path):
            raise KindleNotAttachedError("Kindle is not attached")

        if not os.access(self.mount_path, os.R_OK):
            raise KindleNotReadableError("Kindle is attached but not readable")

        return True

    def get_helpful_message(self, error: Exception) -> str:
        """
        Get a helpful message for the given error.

        Args:
            error: The exception that occurred.

        Returns:
            A helpful message explaining how to resolve the issue.
        """
        if isinstance(error, KindleNotAttachedError):
            return (
                "Kindle device not found!\n\n"
                "Please connect your Kindle device using a USB cable and ensure it's in file transfer mode.\n"
                "You may need to:\n"
                "1. Connect your Kindle via USB\n"
                "2. Select 'Transfer files' when prompted on your Kindle\n"
                "3. Wait for the device to mount\n"
                "4. Try running the application again"
            )
        elif isinstance(error, KindleNotReadableError):
            return (
                "Kindle is connected but not accessible!\n\n"
                "The Kindle device is detected but cannot be read. This might be due to:\n"
                "1. Insufficient permissions - try running with sudo or check file permissions\n"
                "2. Device not in file transfer mode - ensure Kindle is set to 'Transfer files'\n"
                "3. Device is locked - unlock your Kindle and try again\n"
                "4. File system issues - try disconnecting and reconnecting the device"
            )
        else:
            return f"An unexpected error occurred: {str(error)}"

    def find_kindle_mount_paths(self) -> list[str]:
        """
        Find all possible Kindle mount paths for debugging.

        Returns:
            List of paths where Kindle might be mounted.
        """
        found_paths = []
        possible_paths = [
            "/media/Kindle",
            "/media/kindle",
            "/media/*/Kindle",
            "/media/*/kindle",
            "/mnt/Kindle",
            "/mnt/kindle",
            "/run/media/*/Kindle",
            "/run/media/*/kindle",
        ]

        for path in possible_paths:
            if "*" in path:
                import glob

                matches = glob.glob(path)
                for match in matches:
                    found_paths.append(match)
            else:
                if os.path.exists(path):
                    found_paths.append(path)

        return found_paths
