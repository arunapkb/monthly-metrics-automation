"""
WebDriver configuration and setup for Chrome browser.
Handles Chrome options, download settings, and driver initialization.
"""
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config.settings import settings

class WebDriverManager:
    """Manages Chrome WebDriver configuration and lifecycle."""

    def __init__(self):
        self.driver = None
        self.service = None

    def create_chrome_options(self):
        """
        Configure Chrome options for automation.

        Returns:
            Options: Configured Chrome options
        """
        chrome_options = Options()

        # Download preferences
        prefs = {
            "download.default_directory": settings.CHROME_DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Window size and display options
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")

        # Security and stability options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")

        # Optional: Run in headless mode (uncomment if needed)
        # chrome_options.add_argument("--headless")

        return chrome_options

    def setup_driver(self):
        """
        Initialize and configure Chrome WebDriver.

        Returns:
            WebDriver: Configured Chrome WebDriver instance
        """
        try:
            print("Starting: Setting up Chrome WebDriver...")

            # Create Chrome options
            chrome_options = self.create_chrome_options()

            # Setup Chrome service
            self.service = Service(ChromeDriverManager().install())

            # Create WebDriver instance
            self.driver = webdriver.Chrome(service=self.service, options=chrome_options)

            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)

            print(f"Success: WebDriver setup complete")
            print(f"📂 Downloads will be saved to: {settings.CHROME_DOWNLOAD_DIR}")

            return self.driver

        except Exception as e:
            print(f"Failed to setup WebDriver: {e}")
            raise

    def close_driver(self, delay_seconds=20):
        """
        Close the WebDriver with optional delay for downloads.

        Args:
            delay_seconds: Time to wait before closing (for downloads to complete)
        """
        if self.driver:
            try:
                print(f"⏳ Waiting {delay_seconds} seconds for downloads to complete...")
                import time
                time.sleep(delay_seconds)

                print("🔄 Closing browser...")
                self.driver.quit()
                print("Success: Browser closed successfully")
            except Exception as e:
                print(f"⚠️ Error while closing browser: {e}")
            finally:
                self.driver = None

    def __enter__(self):
        """Context manager entry - setup driver."""
        return self.setup_driver()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close driver."""
        self.close_driver()

        # Take screenshot on error for debugging
        if exc_type and self.driver:
            screenshot_path = settings.LOGS_FOLDER / "error_screenshot.png"
            try:
                self.driver.save_screenshot(str(screenshot_path))
                print(f"📸 Error screenshot saved to {screenshot_path}")
            except:
                pass

# Convenience function for quick driver setup
def get_chrome_driver():
    """
    Quick function to get a configured Chrome WebDriver.

    Returns:
        WebDriver: Configured Chrome WebDriver instance
    """
    manager = WebDriverManager()
    return manager.setup_driver()
