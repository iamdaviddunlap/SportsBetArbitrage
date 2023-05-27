import time
from bs4 import BeautifulSoup

import yaml
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from util import get_driver


def parse_page(driver):
    pass


class BarstoolSportsController:
    def __init__(self):
        self.driver = None

    def startup(self):
        self.driver = get_driver()

        self.driver.get('https://www.barstoolsportsbook.com/live')

        # Click over to the "Watch Live" tab to see all live games for all sports
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        x = 1
        # buttons = soup.findAll('div', {'role': 'button'})
        # # watch_live_button = [x for x in buttons  if 'aria-label' in x.attrs.keys() and 'Watch Live' in x.attrs['aria-label']][0]  TODO put back
        # watch_live_button = \
        # [x for x in buttons if 'aria-label' in x.attrs.keys() and 'Baseball' in x.attrs['aria-label']][0]
        # watch_live_button = beautifulsoup_obj_to_selenium(watch_live_button, self.driver)
        # watch_live_button.click()
        #
        # # Wait until the loading dots are no longer present in the DOM.
        # # This checks every 500ms for the disappearance of the elements.
        # WebDriverWait(self.driver, 10).until_not(
        #     EC.presence_of_all_elements_located(
        #         (By.XPATH, "//span[contains(@style, 'background-color: rgb(0, 95, 200);')]"))
        # )

    def place_bet(self, info):
        pass

    def run_main_loop(self):
        pass


if __name__ == '__main__':
    controller = BarstoolSportsController()
    controller.startup()
