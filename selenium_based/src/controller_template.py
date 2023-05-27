import time
from bs4 import BeautifulSoup

import yaml
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from util import get_driver


def parse_page(driver):
    games_dict = {}
    buttons_dict = {}
    return games_dict, buttons_dict


class GenericController:
    def __init__(self, target_sport):
        self.driver = None
        self.target_sport = target_sport
        self.games_dict = None
        self.buttons_dict = None

    def startup(self):
        self.driver = get_driver()

        URL = None  # TODO set this to real URL
        self.driver.get(URL)

    def place_bet(self, team_name, expected_moneyline, bet_amount):
        # TODO implement
        return False

    def run_main_loop(self):
        while True:
            start_time = time.time()
            try:
                games_dict, buttons_dict = parse_page(self.driver)
                print(f'parsed page in {round(time.time() - start_time, 3)}s. games_dict: \n{games_dict}')
                x = 1
            except Exception as e:
                print(f'!!! Got exception after {round(time.time() - start_time, 3)}s: {e}')


if __name__ == '__main__':
    controller = GenericController(target_sport='baseball')
    controller.startup()
    controller.run_main_loop()
