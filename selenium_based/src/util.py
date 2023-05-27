import os
import platform
from enum import Enum

from selenium.common import SessionNotCreatedException
from seleniumwire.undetected_chromedriver.v2 import Chrome, ChromeOptions
from fake_useragent import UserAgent
import chromedriver_autoinstaller


class BookieSite(Enum):
    FANDUEL = 1
    DRAFTKINGS = 2


def get_driver():
    """Make a new Chrome driver"""

    options = ChromeOptions()
    ua = UserAgent()
    userAgent = ua.random
    options.add_argument("--incognito")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f'user-agent={userAgent}')
    # options.add_argument('--headless')
    # options.add_argument("disable-infobars")
    # options.add_argument("--disable-extensions")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--no-sandbox")

    if platform.system() == 'Windows':
        try:
            driver = Chrome(executable_path=os.path.join(os.path.dirname(__file__), 'chromedriver.exe'),
                                      options=options)
        except SessionNotCreatedException:
            path = chromedriver_autoinstaller.install(os.path.dirname(__file__))
            new_path = os.path.join(os.path.dirname(path), '..', 'chromedriver.exe')
            if os.path.exists(new_path):
                os.remove(new_path)

            os.rename(path, new_path)
            os.rmdir(os.path.dirname(path))

            driver = Chrome(executable_path=os.path.join(os.path.dirname(__file__), 'chromedriver.exe'),
                                      options=options)
    else:
        driver = Chrome(options=options)
    return driver