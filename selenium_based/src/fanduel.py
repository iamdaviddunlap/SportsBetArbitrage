import gzip
import json
import re
import time
from time import sleep
from bs4 import BeautifulSoup
import datetime

import yaml
from selenium.webdriver import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from util import get_driver

import pickle
import tqdm


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


def is_relevant_button_alttxt(tag_element):
    return 'to win' in tag_element.attrs['aria-label'] or 'Moneyline' in tag_element.attrs['aria-label']


def parse_page(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    buttons = soup.findAll('div', {'role': 'button'})

    all_relevant_buttons = []
    parent_ul = None

    # Create the buttons_dict that links button objects with the keys from the getMarketPrices requests
    for button_tag in buttons:
        if 'aria-label' in button_tag.attrs.keys() and is_relevant_button_alttxt(button_tag):
            all_relevant_buttons.append(button_tag)
            if parent_ul is None:
                parent_ul = button_tag.find_parent('ul')

    # We can assume that the first element of the ul will contain the sport's title
    sport_name_class_set = set(parent_ul.next.next.attrs['class'])
    cur_sport = None
    list_parents = [x.find_parent('li') for x in all_relevant_buttons]
    games_dict = dict()
    for li_item in parent_ul.children:
        if set(li_item.next.attrs['class']) == sport_name_class_set:
            # This li_item is the name of a new sport
            cur_sport = str(list(li_item.descendants)[-1])
            cur_sport = ' '.join([x for x in cur_sport.split(' ') if x.lower() != 'live'])
            if cur_sport not in games_dict:  # Check if the sport is already a key in games_dict
                games_dict[cur_sport] = []  # If not, create an empty list for it
        else:
            if li_item in list_parents:
                accessible_divs = li_item.find_all('div', attrs={"aria-label": True, "aria-hidden": False})
                accessible_spans = li_item.find_all('span', attrs={"aria-label": True, "aria-hidden": False})

                cur_relevant_buttons = [x for x in accessible_divs if is_relevant_button_alttxt(x)]
                cur_relevant_labels = [x for x in accessible_spans if any(x.attrs['aria-label'] in s for s in [x.attrs['aria-label'] for x in cur_relevant_buttons])]

                if len(cur_relevant_buttons) != len(cur_relevant_labels):
                    raise Exception(f'Mismatch when parsing. Got a different number of button and label elements. '
                                    f'Buttons: \n{cur_relevant_buttons}\nLabels: \n{cur_relevant_labels}')

                odds_list = []
                for x in cur_relevant_buttons:
                    odds = None if 'aria-disabled' in x.attrs else str(list(x.descendants)[-1])
                    if odds is not None and len(odds) > 6:
                        odds = str(list(x.next.descendants)[-1])
                    odds_list.append(odds)

                cur_game_dict = dict()
                for i in range(len(cur_relevant_buttons)):
                    cur_game_dict[cur_relevant_labels[i].attrs['aria-label']] = odds_list[i]
                games_dict[cur_sport].append(cur_game_dict)
    return games_dict


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
    # watch_live_button = [x for x in buttons  if 'aria-label' in x.attrs.keys() and 'Watch Live' in x.attrs['aria-label']][0]  TODO put back
    watch_live_button = [x for x in buttons  if 'aria-label' in x.attrs.keys() and 'Baseball' in x.attrs['aria-label']][0]
    watch_live_button = beautifulsoup_obj_to_selenium(watch_live_button, driver)
    watch_live_button.click()

    # Wait until the loading dots are no longer present in the DOM.
    # This checks every 500ms for the disappearance of the elements.
    WebDriverWait(driver, 10).until_not(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//span[contains(@style, 'background-color: rgb(0, 95, 200);')]"))
    )

    history = None
    while True:
        start = time.time()
        try:
            games_dict = parse_page(driver)
            if history is None or history != games_dict:
                history = games_dict
                print(f'Refreshed in {round(time.time()-start, 3)}s. games_dict:\n{games_dict}')
        except Exception as e:
            print(f'Got exception: {e}')
        x = 1
    x = 1



    ##### MY FIRST TRY IS BELOW, MOST OR ALL OF THIS SHOULD BE DELETED LATER

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
