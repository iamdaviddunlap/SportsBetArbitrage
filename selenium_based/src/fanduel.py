import os
import pickle
import platform
import re

import requests
import yaml
from selenium.common import SessionNotCreatedException
# from seleniumwire import webdriver
from seleniumwire.undetected_chromedriver.v2 import Chrome, ChromeOptions
from fake_useragent import UserAgent
import chromedriver_autoinstaller
from selenium_stealth import stealth
import ast
import gzip
import json
import re
from time import sleep
from bs4 import BeautifulSoup
import datetime

import requests
import yaml
from selenium.webdriver import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import pickle
import tqdm

with open('credentials.yaml') as f:
    credentials = yaml.safe_load(f)
# API_KEY = credentials['API_KEY']

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



def get_driver():
    """Make a new Chrome driver"""
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


def beautifulsoup_obj_to_selenium(bs_obj, driver):
    css_selector = '.'+'.'.join(bs_obj.attrs['class'])
    sel_objs = driver.find_elements(By.CSS_SELECTOR, css_selector)
    if len(sel_objs) > 1:
        for obj in sel_objs:
            bs_obj_name = bs_obj.attrs['aria-label'].replace('  ',  ' ').strip().lower()
            sel_obj_name = obj.accessible_name.replace('  ',  ' ').strip().lower()
            if bs_obj_name == sel_obj_name:
                return obj
        raise Exception('Error finding selenium obj from BS obj: multiple objs found from class, could not disambiguate with accessible_name')
    else:
        return sel_objs[0]


def main():
    driver = get_driver()

    with open('credentials.yaml') as f:
        credentials = yaml.safe_load(f)
    username = credentials['username']
    password = credentials['password']

    driver.get('https://co.sportsbook.fanduel.com/live?tab=watch-live')

    # Click over to the "Watch Live" tab to see all live games for all sports
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    buttons = soup.findAll('div', {'role': 'button'})
    watch_live_button = [x for x in buttons  if 'aria-label' in x.attrs.keys() and 'Watch Live' in x.attrs['aria-label']][0]
    watch_live_button = beautifulsoup_obj_to_selenium(watch_live_button, driver)
    watch_live_button.click()

    # Wait until the loading dots are no longer present in the DOM.
    # This checks every 500ms for the disappearance of the elements.
    WebDriverWait(driver, 10).until_not(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//span[contains(@style, 'background-color: rgb(0, 95, 200);')]"))
    )

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    buttons = soup.findAll('div', {'role': 'button'})

    # Extract the price_dict info from the getMarketPrices requests
    reqs = driver.requests
    most_recent_req = [x for x in reqs if 'getMarketPrices' in x.url][-1]
    price_json = json.loads(gzip.decompress(most_recent_req.response.body).decode('utf-8'))
    price_dict = {x['marketId']: [y['winRunnerOdds']['americanDisplayOdds']['americanOddsInt'] for y in x['runnerDetails']] for x in price_json}

    # Create the buttons_dict that links button objects with the keys from the getMarketPrices requests
    buttons_dict = {k: [None]*2 for k in price_dict.keys()}
    for button_tag in buttons:
        if 'aria-label' in button_tag.attrs.keys() and ('to win' in button_tag.attrs['aria-label'] or 'Moneyline' in button_tag.attrs['aria-label']):
            odds_amount = int(button_tag.next.next)
            for market_id, odds_lst in price_dict.items():
                if odds_amount in odds_lst:
                    buttons_dict[market_id][odds_lst.index(odds_amount)] = button_tag

    # While loop to look for updates to the price_dict
    last_date = datetime.datetime.now()
    while True:
        last_req = [x for x in driver.requests if 'getMarketPrices' in x.url][-1]
        if last_req.response is not None and last_req.date > last_date:
            last_date = last_req.date
            price_json = json.loads(gzip.decompress(last_req.response.body).decode('utf-8'))
            price_dict_new = {x['marketId']: [None if y['runnerStatus'] != 'ACTIVE' else y['winRunnerOdds']['americanDisplayOdds']['americanOddsInt']
                                              for y in x['runnerDetails']] for x in price_json}
            print(price_dict_new)
            driver.requests.clear()
            break  # TODO don't actually break here. Move this while loop to a thread and continuously update the dict

    # TODO use different code to determine what's a "relevant button"
    relevant_button = buttons_dict[list(buttons_dict.keys())[0]][1]

    # Click the relevant button
    button_selenium = beautifulsoup_obj_to_selenium(relevant_button, driver)
    button_selenium.click()

    # Enter the be amount into the input
    bet_amount = 10  # TODO set this elsewhere
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    wager_input_tag = [x for x in soup.findAll('input', {'type': 'text'}) if x.parent.parent.next.next == 'WAGER'][0]
    input_obj_selenium = beautifulsoup_obj_to_selenium(wager_input_tag, driver)
    input_obj_selenium.send_keys(str(bet_amount))

    x = 1

    return
    ###### IAN CODE FOR YOUTUBE LOGIN #####

    driver.get('https://accounts.google.com/servicelogin')
    search_form = driver.find_element(By.ID, 'identifierId')
    sleep(1)
    search_form.send_keys(username)
    next_button = driver.find_element(By.XPATH, '//*[@id ="identifierNext"]')
    next_button.click()
    WebDriverWait(driver, 45).until(
        EC.presence_of_element_located((By.NAME, "Passwd")),
    )
    search_form = driver.find_element(By.NAME, 'Passwd')
    sleep(1)
    search_form.send_keys(password)
    search_form.send_keys(Keys.RETURN)
    WebDriverWait(driver, 45).until(
        EC.url_matches('https\:\/\/myaccount\.google\.com\/\?utm_source\=sign_in_no_continue'),
    )

    # url = 'https://myactivity.google.com/product/youtube?hl=en&utm_medium=web&utm_source=youtube&pli=1&max=1451615325000000'
    # url = 'https://myactivity.google.com/product/youtube?hl=en&utm_medium=web&utm_source=youtube&pli=1&max=1514789750000000'
    url = 'https://myactivity.google.com/product/youtube?hl=en&utm_medium=web&utm_source=youtube&pli=1'

    driver.get(url)
    num_batches = len(driver.requests)

    i = 0
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(0.5)

        if i % 200 == 0:
            new_num_batches = len(driver.requests)
            if not new_num_batches > num_batches:
                break
            else:
                num_batches = new_num_batches

        i += 1

    total_history = list()
    for request in tqdm([request for request in driver.requests if
             ('myactivity' in request.url and 'batchexecute' in request.url)]):
        try:
            s = gzip.decompress(request.response.body).decode('utf-8')
            idxs = [a.start() for a in re.finditer('\n', s)]
            s = s[idxs[2]+1:idxs[3]]
            history = json.loads(json.loads(s)[0][2])[0]
            history = [h for h in history if (len(h[9]) == 4 and h[9][2] == 'Watched')]
            total_history.extend(history)
        except Exception:
            pass

    # total_history = sorted(total_history, key=lambda x: x[4])[::2]
    with open('data/total_history_4', 'wb') as fp:
        pickle.dump(total_history, fp)
    x=1

    # wait = WebDriverWait(driver, 10)
    #
    # try:
    #     # need the inner request that contains coordinates and timestamp
    #     wait.until(lambda d: len(d.current_url.split('/')[4]) > 1)
    # )


if __name__ == '__main__':
    main()
