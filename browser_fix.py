import os, platform
import subprocess
import time, logging, psutil, requests
import undetected_chromedriver as webdriver
from selenium.webdriver.common.by import By
from selenium import webdriver as selenium_webdriver
from osquery_agent import OSQueryAgent
from bs4 import BeautifulSoup as bs
from notifications import Notification

_LOGGER = logging.getLogger(__name__)

# browser_fix.py

# Compatibility:
# Google Chrome

# Pre-requisites
# Google Chrome


class BrowserFix:
    def __init__(self, browser):
        self.driver = ""
        self.options = webdriver.ChromeOptions()
        self.browser = browser
        self.osquery_agent = OSQueryAgent()
        self.notification = Notification()
        self.selenium_webdriver = ""
        self.selenium_options = selenium_webdriver.ChromeOptions()


    def close_browser(self):
        self.notification.create_notification(f"{self.browser} will close in 1 minute to run self-heal script. Please save your current work.", False)
        time.sleep(60)

        # to close (every window whose visible is true)
        # Execute AppleScript to close Chrome
        script = f'tell application "{self.browser}" to quit'
        subprocess.run(["osascript", "-e", script])

        # Give some time for Chrome to close before quitting
        time.sleep(2)

        # Execute AppleScript to quit Chrome
        # script = f'tell application "{self.browser}" to quit'
        script = f'tell my application "{self.browser}" to if it is running then quit'
        subprocess.run(["osascript", "-e", script])

        time.sleep(2)

        self.check_browser_not_running()

    def check_browser_not_running(self):
        chrome_running = False
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.name() == self.browser:
                chrome_running = True

        if chrome_running:
            self.close_browser()

        return False

    def delete_cookies_cache(self):
        browser_running = self.check_browser_not_running()
        # browser_running = False

        if not browser_running:
            try:
                print("ENTERED HERE")
                user_path = os.path.expanduser("~")
                user_data_dir = os.path.join(user_path, "Library/Application Support/Google/Chrome/Profile 2")

                self.options.add_argument(f"user-data-dir={user_data_dir}")
                self.options.add_argument(r'--profile-directory=Default')

                self.selenium_options.add_argument(f"user-data-dir={user_data_dir}")
                self.selenium_options.add_argument(r'--profile-directory=Default')

                self.selenium_webdriver = webdriver.Chrome(options=self.selenium_options)
                self.selenium_webdriver.get("chrome://settings/clearBrowserData")
                time.sleep(5)

                clear_data_button_script = """return document.querySelector("body > settings-ui").shadowRoot.querySelector("#main").shadowRoot.querySelector(
                    "settings-basic-page").shadowRoot.querySelector(
                    "#basicPage > settings-section:nth-child(11) > settings-privacy-page").shadowRoot.querySelector(
                    "settings-clear-browsing-data-dialog").shadowRoot"""

                checkboxes_script = """return document.querySelector("body > settings-ui").shadowRoot.querySelector("#main").
                shadowRoot.querySelector("settings-basic-page").shadowRoot.querySelector("#basicPage > settings-section:nth-child(11) > settings-privacy-page").
                shadowRoot.querySelector("settings-clear-browsing-data-dialog").shadowRoot.querySelector("#browsingCheckboxBasic").shadowRoot.querySelector("#checkbox").
                shadowRoot"""

                clear_data_button_shadow_root = self.selenium_webdriver.execute_script(clear_data_button_script)
                checkboxes_shadow_root = self.selenium_webdriver.execute_script(checkboxes_script)

                clear_data_button = clear_data_button_shadow_root.find_element(By.ID, "clearBrowsingDataConfirm")

                # Ensure the browsing history is not cleared
                browsing_history_checkbox = checkboxes_shadow_root.find_element(By.ID, "checkbox")
                # Un-tick the browser history checkbox
                history_selected = browsing_history_checkbox.is_selected()

                if history_selected is True:
                    browsing_history_checkbox.click()

                time.sleep(15)
                # Clear cookies and cache
                clear_data_button.click()

            finally:
                _LOGGER.info("Web Driver has been closed.")
                self.selenium_webdriver.close()

    def check_for_browser_update(self):
        # Web scrape the latest version and compare
        browser_version = self.osquery_agent.check_current_browser_version()

        if browser_version is not None:
            versions_url = "https://www.whatismybrowser.com/guides/the-latest-version/chrome"
            response = requests.request("GET", versions_url)

            soup = bs(response.text, 'html.parser')
            rows = soup.select('td strong')
            # Find version
            latest_version = {'macos': rows[1].parent.next_sibling.next_sibling.text}
            # Web scrape the latest version
            current_version_number = browser_version.split(" ")[2]
            print("checking browser version on client", current_version_number)
            print("latest version on mac",latest_version['macos'])

            if current_version_number >= latest_version['macos']:
                _LOGGER.info("Chrome browser up-to-date")
                return True
            return False
        _LOGGER.debug("Unable to find Chrome version")

    def try_alternative_browser(self, browser_updated):
        """I can crash chrome - now I need to be able to see what crashed chrome and try it in another browser"""
        if browser_updated:
            self.notification.create_notification(f"Cache & Cookies in {self.browser} have been cleared and browser is up to date. You could try a different browser.", False)
        else:
            self.notification.create_notification(f"Cache & Cookies in {self.browser} have been cleared. You need to update it.", False)


if __name__ == "__main__":
    bot = BrowserFix("Google Chrome")
    _LOGGER.info("Browser Fix Script started.")
    # Delete cookies & cache from Google Chrome
    bot.delete_cookies_cache()
    print("Cookies have been deleted")
    # Check the browser version is up-to-date
    browser_check = bot.check_for_browser_update()
    print("Browser version checked")
    # Send notification to user to try a new browser or to update browser if out of date
    print("browser_check", browser_check)
    bot.try_alternative_browser(browser_check)
