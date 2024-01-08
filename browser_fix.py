import time, logging, psutil, requests
import undetected_chromedriver as webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from osquery_agent import OSQueryAgent
from bs4 import BeautifulSoup as bs
from notifications import Notification

_LOGGER = logging.getLogger(__name__)

class BrowserFix:
    def __init__(self):
        self.driver = ""
        self.options = webdriver.ChromeOptions()
        self.browser = "Google Chrome"
        self.osquery_agent = OSQueryAgent()
        self.notification = Notification()

    def check_browser_not_running(self):
        for proc in psutil.process_iter(['pid', 'name']):
            print("process name", proc.name())
            if proc.name() == self.browser:
                return True

        return False

    def perform_actions(self, keys: str):
        actions = ActionChains(self.driver)
        actions.send_keys(keys)
        time.sleep(2)
        print("actions ran")
        actions.perform()

    def delete_cookies_cache(self):
        browser_running = self.check_browser_not_running()
        print(browser_running, "check")

        if not browser_running:
            user_data_dir = r"/Users/sunilsamra/Library/Application Support/Google/Chrome/Profile 2"

            self.options.add_argument(f"user-data-dir={user_data_dir}")
            self.options.add_argument(r'--profile-directory=Default')
            self.driver = webdriver.Chrome(options=self.options, use_subprocess=True)
            self.driver.get("chrome://settings/clearBrowserData")
            self.driver.implicitly_wait(2)

            self.perform_actions(Keys.TAB * 7 + Keys.ENTER + Keys.TAB * 6 + Keys.ENTER)
            time.sleep(30)
            self.driver.close()

    def check_for_browser_update(self):
        # Web scrape the latest version and compare
        browser_version = self.osquery_agent.check_current_browser_version()

        if browser_version is not None:
            chrome_versions_url = "https://www.whatismybrowser.com/guides/the-latest-version/chrome"
            response = requests.request("GET", chrome_versions_url)

            soup = bs(response.text, 'html.parser')
            rows = soup.select('td strong')
            # Find version or assume it is MAC?
            latest_version = {'macos': rows[1].parent.next_sibling.next_sibling.text}
            # Web scrape the latest version
            current_version_number = browser_version.split(" ")[2]
            print("checking browser version on client", current_version_number)
            print("latest version on mac",latest_version['macos'])

            if current_version_number == latest_version['macos']:
                _LOGGER.info("Chrome browser up-to-date")
                return True
            return False

        _LOGGER.debug("Unable to find Chrome version")

    def try_alternative_browser(self, browser_updated):
        """I can crash chrome - now I need to be able to see what crashed chrome and try it in another browser"""
        if browser_updated:
            self.notification.create_notification_2("We have cleared your cache & cookies in Google Chrome. \nYour browser version is up to date.\nIf problems persist, please try a new browser.", False)
        else:
            self.notification.create_notification_2("We have cleared your cache & cookies in Google Chrome.\n Your browser version is out of date and may be the cause problems of websites not being able to load.\nPlease update your browser.", False)


if __name__ == "__main__":
    bot = BrowserFix()
    _LOGGER.info("Browser Fix Script started.")
    # Delete cookies & cache from Google Chrome
    bot.delete_cookies_cache()
    print("cookies deleted")
    # Check the browser version is up-to-date
    browser_check = bot.check_for_browser_update()
    print("browser version checked")
    # Send notification to user to try a new browser or to update browser if out of date
    print("browser_check", browser_check)
    bot.try_alternative_browser(browser_check)
