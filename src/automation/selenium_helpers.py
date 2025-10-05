"""
Selenium helper utilities for web automation.
Provides robust, reusable functions for common Selenium operations.
"""
import time

from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumHelpers:
    """Collection of robust Selenium helper methods."""

    @staticmethod
    def safe_click(driver, by, value, timeout=20, retries=3):
        """
        Waits for an element, scrolls to it, and performs a robust JS click.
        Includes retry mechanism for StaleElementReferenceException.

        Args:
            driver: WebDriver instance
            by: Selenium By locator type
            value: Element selector value
            timeout: Maximum time to wait for element (default: 20s)
            retries: Number of retry attempts (default: 3)
        """
        for attempt in range(retries):
            try:
                wait = WebDriverWait(driver, timeout)
                element = wait.until(EC.element_to_be_clickable((by, value)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", element)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", element)
                print(f"Success: Clicked on element: '{value}' on attempt {attempt + 1}")
                return
            except StaleElementReferenceException:
                print(f"⚠StaleElementReferenceException on attempt {attempt + 1}/{retries} for '{value}'. Retrying...")
                time.sleep(1)
            except TimeoutException:
                print(f"ERROR: Timed out waiting for element to be clickable: '{value}'")
                raise

        raise Exception(f"FAILED to click element '{value}' after {retries} attempts.")

    @staticmethod
    def safe_send_keys(driver, by, value, keys, timeout=10, clear_first=True):
        """
        Waits for an element, clicks it, optionally clears it, and sends keys.

        Args:
            driver: WebDriver instance
            by: Selenium By locator type
            value: Element selector value
            keys: Text to send to element
            timeout: Maximum time to wait (default: 10s)
            clear_first: Whether to clear existing text (default: True)
        """
        try:
            wait = WebDriverWait(driver, timeout)
            element = wait.until(EC.visibility_of_element_located((by, value)))
            element.click()
            time.sleep(0.2)

            if clear_first:
                element.send_keys(Keys.CONTROL + "a")
                element.send_keys(Keys.DELETE)

            element.send_keys(keys)
            print(f"Success: Typed keys into element: '{value}'")
        except TimeoutException:
            print(f"ERROR: Timed out waiting for element to be visible: '{value}'")
            raise

    @staticmethod
    def wait_for_element(driver, by, value, timeout=10, condition='visibility'):
        """
        Wait for an element with specified condition.

        Args:
            driver: WebDriver instance
            by: Selenium By locator type
            value: Element selector value
            timeout: Maximum time to wait (default: 10s)
            condition: Type of condition to wait for ('visibility', 'presence', 'clickable')

        Returns:
            WebElement if found
        """
        wait = WebDriverWait(driver, timeout)

        conditions = {'visibility': EC.visibility_of_element_located, 'presence': EC.presence_of_element_located,
                      'clickable': EC.element_to_be_clickable}

        if condition not in conditions:
            raise ValueError(f"Invalid condition: {condition}. Must be one of {list(conditions.keys())}")

        try:
            element = wait.until(conditions[condition]((by, value)))
            print(f"Success: Element found: '{value}'")
            return element
        except TimeoutException:
            print(f"ERROR: Timed out waiting for element: '{value}'")
            raise

    @staticmethod
    def wait_for_page_load(driver, timeout=30):
        """
        Wait for page to complete loading.

        Args:
            driver: WebDriver instance
            timeout: Maximum time to wait (default: 30s)
        """
        try:
            WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
            print("Success: Page loaded successfully")
        except TimeoutException:
            print("⚠Page load timeout - continuing anyway")

    @staticmethod
    def switch_to_new_tab(driver, timeout=15):
        """
        Wait for a new tab to open and switch to it.

        Args:
            driver: WebDriver instance
            timeout: Maximum time to wait (default: 15s)

        Returns:
            str: Title of the new tab
        """
        try:
            WebDriverWait(driver, timeout).until(EC.number_of_windows_to_be(2))
            driver.switch_to.window(driver.window_handles[-1])
            title = driver.title
            print(f"Success: Switched to new tab: {title}")
            return title
        except TimeoutException:
            print("ERROR: No new tab opened within timeout")
            raise

    @staticmethod
    def take_screenshot(driver, filepath):
        """
        Take a screenshot for debugging purposes.

        Args:
            driver: WebDriver instance
            filepath: Path to save screenshot
        """
        try:
            driver.save_screenshot(filepath)
            print(f"Screenshot saved to {filepath}")
        except Exception as e:
            print(f"Failed to save screenshot: {e}")
