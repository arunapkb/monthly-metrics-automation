"""
Configuration settings for Jira Automation Project.
Handles environment variables and application constants.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

class Settings:
    """Application settings and configuration."""

    def __init__(self):
        # Load environment variables
        self._load_environment()

        # Project paths
        self.PROJECT_ROOT = Path(__file__).parent.parent
        self.DOWNLOADS_FOLDER = self.PROJECT_ROOT / "downloads"
        self.CREDENTIALS_FOLDER = self.PROJECT_ROOT / "credentials"
        self.LOGS_FOLDER = self.PROJECT_ROOT / "logs"

        # Create necessary directories
        self._create_directories()

        # Google Drive configuration
        self.GOOGLE_SCOPES = ["https://www.googleapis.com/auth/drive"]
        self.CREDENTIALS_FILE = self.CREDENTIALS_FOLDER / "credentials.json"
        self.TOKEN_FILE = self.CREDENTIALS_FOLDER / "token.json"
        self.DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

        # JumpCloud configuration
        self.JUMPCLOUD_EMAIL = os.getenv("JC_USERNAME")
        self.JUMPCLOUD_PASSWORD = os.getenv("JC_PASSWORD")

        # Jira configuration
        self.JIRA_SEARCH_URL = os.getenv("JIRA_SEARCH_URL")
        self.JQL_QUERY = os.getenv("JQL_QUERY")

        # Selenium configuration
        self.CHROME_DOWNLOAD_DIR = str(self.DOWNLOADS_FOLDER.absolute())
        self.SELENIUM_TIMEOUT = 20
        self.MFA_TIMEOUT = 60

    def _load_environment(self):
        """Load environment variables from .env file."""
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        else:
            print("⚠️ Warning: .env file not found. Please create one based on .env.example")

    def _create_directories(self):
        """Create necessary project directories."""
        directories = [self.DOWNLOADS_FOLDER, self.CREDENTIALS_FOLDER, self.LOGS_FOLDER]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def validate_credentials(self):
        """Validate that required credentials are available."""
        required_vars = [('JC_USERNAME', self.JUMPCLOUD_EMAIL), ('JC_PASSWORD', self.JUMPCLOUD_PASSWORD),
            ('JIRA_SEARCH_URL', self.JIRA_SEARCH_URL), ('JQL_QUERY', self.JQL_QUERY),
            ('DRIVE_FOLDER_ID', self.DRIVE_FOLDER_ID)]

        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        return True

# Create a global settings instance
settings = Settings()
