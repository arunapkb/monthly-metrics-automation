"""
Jira operations module.
Handles JQL queries, search operations, and CSV exports.
"""
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from config.settings import settings
from src.automation.selenium_helpers import SeleniumHelpers
from src.utils.file_operations import FileOperations


class JiraOperations:
    """Handles Jira-specific operations and exports."""

    def __init__(self, driver):
        """
        Initialize Jira operations.

        Args:
            driver: WebDriver instance
        """
        self.driver = driver
        self.helpers = SeleniumHelpers()
        self.file_ops = FileOperations()

    def execute_jql_and_export(self, jira_url=None, jql_query=None):
        """
        Execute JQL query and export results as CSV.

        Args:
            jira_url: Jira search URL (uses config default if None)
            jql_query: JQL query string (uses config default if None)

        Returns:
            str: Path to the exported CSV file
        """
        # Use provided parameters or fall back to config
        jira_url = jira_url or settings.JIRA_SEARCH_URL
        jql_query = jql_query or settings.JQL_QUERY

        if not jira_url or not jql_query:
            raise ValueError("Jira URL and JQL query must be provided")

        try:
            print("\nStarting: Starting JQL export workflow...")

            # Navigate to Jira search
            self._navigate_to_search(jira_url)

            # Switch to JQL mode
            self._ensure_jql_mode()

            # Execute query
            self._execute_jql_query(jql_query)

            # Export CSV
            exported_file = self._export_csv()

            print("\nSuccess: JQL export completed successfully!")
            return exported_file

        except Exception as e:
            print(f"JQL export failed: {e}")
            raise

    def _navigate_to_search(self, jira_url):
        """Navigate to Jira search page."""
        print(f"🌐 Navigating to Jira search: {jira_url}")
        self.driver.get(jira_url)
        self.helpers.wait_for_page_load(self.driver)

    def _ensure_jql_mode(self):
        """Ensure JQL mode is active."""
        print("🔧 Ensuring JQL mode is active...")

        try:
            # Try to click JQL button (short timeout)
            jql_button_xpath = "//button[span[text()='JQL']]"
            self.helpers.safe_click(self.driver, By.XPATH, jql_button_xpath, timeout=5)
            print("Success: Switched to JQL mode")
        except (TimeoutException, Exception):
            print("Success: JQL mode already active")

    def _execute_jql_query(self, jql_query):
        """Execute the JQL query."""
        print(f"📝 Executing JQL query: {jql_query}")

        # Enter JQL query
        jql_editor_selector = "div[data-testid='jql-editor-input']"
        self.helpers.safe_send_keys(self.driver, By.CSS_SELECTOR, jql_editor_selector, jql_query)

        # Submit query
        search_button_selector = "button[data-testid='jql-editor-search']"
        self.helpers.safe_click(self.driver, By.CSS_SELECTOR, search_button_selector)

        print("Success: JQL query executed")

        # Wait a moment for results to load
        time.sleep(3)

    def _export_csv(self):
        """Export search results as CSV."""
        print("📤 Exporting results to CSV...")

        # Wait for export button and click it
        export_button_xpath = "//button[@data-testid='issue-navigator-action-export-issues.ui.filter-button--trigger']"
        self.helpers.safe_click(self.driver, By.XPATH, export_button_xpath)

        # Short pause for dropdown menu
        time.sleep(1)

        # Click CSV export option
        csv_export_xpath = "//span[text()='Export CSV (my defaults)']"
        self.helpers.safe_click(self.driver, By.XPATH, csv_export_xpath)

        print("Success: CSV export initiated")

        # Wait and rename the downloaded file
        return self._handle_downloaded_file()

    def _handle_downloaded_file(self):
        """Handle the downloaded CSV file."""
        print("⏳ Waiting for file download to complete...")
        time.sleep(15)  # Wait for download

        # Find and rename the latest file
        renamed_file = self.file_ops.find_and_rename_latest_file(download_dir=settings.DOWNLOADS_FOLDER,
            new_name_prefix="Jira_Report")

        if renamed_file:
            print(f"Success: File successfully processed: {renamed_file.name}")
            return renamed_file
        else:
            raise Exception("Failed to process downloaded file")

    def get_search_results_count(self):
        """
        Get the number of search results.

        Returns:
            int: Number of search results, or None if not found
        """
        try:
            # Look for results count element (this may vary based on Jira version)
            count_selectors = [".issue-list-count", "[data-testid='issue-count']", ".search-results-count"]

            for selector in count_selectors:
                try:
                    element = self.helpers.wait_for_element(self.driver, By.CSS_SELECTOR, selector, timeout=5)
                    count_text = element.text
                    # Extract number from text like "Showing 1-50 of 234 issues"
                    import re
                    numbers = re.findall(r'\d+', count_text)
                    if numbers:
                        return int(numbers[-1])  # Return the last number (total count)
                except:
                    continue

            print("⚠️ Could not determine search results count")
            return None

        except Exception as e:
            print(f"⚠️ Error getting search results count: {e}")
            return None

    def validate_query_syntax(self, jql_query):
        """
        Basic JQL query syntax validation.

        Args:
            jql_query: JQL query string to validate

        Returns:
            bool: True if syntax appears valid
        """
        if not jql_query or not jql_query.strip():
            return False

        # Basic checks
        query = jql_query.strip()

        # Check for common JQL keywords
        jql_keywords = ['project', 'status', 'assignee', 'created', 'updated', 'reporter', 'priority']
        has_keyword = any(keyword.lower() in query.lower() for keyword in jql_keywords)

        # Check for balanced quotes
        single_quotes = query.count("'")
        double_quotes = query.count('"')

        balanced_quotes = (single_quotes % 2 == 0) and (double_quotes % 2 == 0)

        return has_keyword and balanced_quotes
