"""
JumpCloud authentication module.
Handles login, MFA, and session management for JumpCloud.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException

from config.settings import settings
from src.automation.selenium_helpers import SeleniumHelpers

class JumpCloudAuth:
    """Handles JumpCloud authentication workflow."""

    def __init__(self, driver):
        """
        Initialize JumpCloud authentication.

        Args:
            driver: WebDriver instance
        """
        self.driver = driver
        self.helpers = SeleniumHelpers()

        # Validate credentials
        if not settings.JUMPCLOUD_EMAIL or not settings.JUMPCLOUD_PASSWORD:
            raise ValueError("JumpCloud credentials not found in environment variables")

    def login(self):
        """
        Perform complete JumpCloud login including MFA if required.

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            print("Starting: Starting JumpCloud login process...")

            # Navigate to JumpCloud
            self._navigate_to_jumpcloud()

            # Enter credentials
            self._enter_credentials()

            # Handle MFA if present
            self._handle_mfa()

            # Wait for dashboard
            self._wait_for_dashboard()

            print("Success: JumpCloud login completed successfully")
            return True

        except Exception as e:
            print(f"JumpCloud login failed: {e}")
            return False

    def _navigate_to_jumpcloud(self):
        """Navigate to JumpCloud login page."""
        print("🌐 Navigating to JumpCloud...")
        self.driver.get("https://console.jumpcloud.com/userconsole")
        self.helpers.wait_for_page_load(self.driver)

    def _enter_credentials(self):
        """Enter email and password credentials."""
        print("📧 Entering email...")
        self.helpers.safe_send_keys(
            self.driver, 
            By.NAME, 
            "email", 
            settings.JUMPCLOUD_EMAIL
        )

        # Click login button after email
        self.helpers.safe_click(
            self.driver,
            By.CSS_SELECTOR,
            'button[data-automation="loginButton"]'
        )

        print("🔐 Entering password...")
        self.helpers.safe_send_keys(
            self.driver,
            By.NAME,
            "password",
            settings.JUMPCLOUD_PASSWORD
        )

        # Click login button after password
        self.helpers.safe_click(
            self.driver,
            By.CSS_SELECTOR,
            'button[data-automation="loginButton"]'
        )

        print("🔑 Credentials submitted")

    def _handle_mfa(self):
        """Handle Multi-Factor Authentication if present."""
        try:
            print("🔐 Checking for MFA prompt...")

            # Look for JumpCloud Protect MFA button
            mfa_button_xpath = "//span[contains(text(), 'JumpCloud Protect')]/ancestor::div[1]"

            wait = WebDriverWait(self.driver, 10)
            mfa_button = wait.until(ec.visibility_of_element_located((By.XPATH, mfa_button_xpath)))

            # Click MFA button
            self.driver.execute_script("arguments[0].click();", mfa_button)
            print("Success: MFA push notification sent. Please approve on your device...")

            # Wait longer for MFA approval
            print(f"⏳ Waiting up to {settings.MFA_TIMEOUT} seconds for MFA approval...")

        except TimeoutException:
            print("ℹ️ No MFA prompt detected, continuing...")

    def _wait_for_dashboard(self):
        """Wait for JumpCloud dashboard to load."""
        print("⏳ Waiting for JumpCloud dashboard to load...")

        try:
            # Wait for search input (indicates dashboard is loaded)
            WebDriverWait(self.driver, settings.MFA_TIMEOUT).until(
                ec.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="search"]'))
            )
            print("Success: JumpCloud dashboard loaded")

        except TimeoutException:
            raise Exception("Dashboard failed to load within timeout period")

    def navigate_to_app(self, app_search_term, app_selector):
        """
        Navigate to a specific application from JumpCloud dashboard.

        Args:
            app_search_term: Text to search for the app
            app_selector: CSS selector for the app link

        Returns:
            str: Title of the new tab/window
        """
        try:
            print(f"🔍 Searching for '{app_search_term}' application...")

            # Search for the application
            self.helpers.safe_send_keys(
                self.driver,
                By.CSS_SELECTOR,
                'input[type="search"]',
                app_search_term
            )

            # Click on the application
            self.helpers.safe_click(self.driver, By.CSS_SELECTOR, app_selector)

            # Switch to new tab
            new_tab_title = self.helpers.switch_to_new_tab(self.driver)

            print(f"Success: Successfully navigated to {app_search_term}")
            return new_tab_title

        except Exception as e:
            print(f"Failed to navigate to {app_search_term}: {e}")
            raise

    def navigate_to_jira(self):
        """
        Navigate to Jira from JumpCloud dashboard.

        Returns:
            str: Title of the Jira tab
        """
        print("🎯 Navigating to Jira from JumpCloud...")

        return self.navigate_to_app(
            app_search_term="atlassian",
            app_selector='a[href*="sso.jumpcloud.com/saml2/atlassiancloud"]'
        )
