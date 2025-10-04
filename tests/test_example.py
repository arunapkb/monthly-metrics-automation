"""
Example test file for Jira Automation Project.
Run with: pytest tests/
"""
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.utils.file_operations import FileOperations

class TestSettings:
    """Test the Settings class."""

    def test_settings_initialization(self):
        """Test that settings can be initialized."""
        settings = Settings()
        assert settings.PROJECT_ROOT is not None
        assert settings.DOWNLOADS_FOLDER is not None
        assert settings.SELENIUM_TIMEOUT == 20

class TestFileOperations:
    """Test the FileOperations class."""

    def test_ensure_directory_exists(self):
        """Test directory creation."""
        test_dir = Path("test_temp_dir")

        # Create directory
        result = FileOperations.ensure_directory_exists(test_dir)

        # Verify it exists
        assert result.exists()
        assert result.is_dir()

        # Clean up
        result.rmdir()

    def test_get_file_info_nonexistent(self):
        """Test file info for non-existent file."""
        result = FileOperations.get_file_info("non_existent_file.txt")
        assert result is None

if __name__ == "__main__":
    pytest.main([__file__])
