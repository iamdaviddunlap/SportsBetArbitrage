import time
from bs4 import BeautifulSoup
import json

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from util import get_driver, BookieSite


def beautifulsoup_obj_to_selenium(bs_obj, driver):
    css_selector = '.' + '.'.join(bs_obj.attrs['class'])
    sel_objs = driver.find_elements(By.CSS_SELECTOR, css_selector)
    if len(sel_objs) > 1:
        for obj in sel_objs:
            bs_obj_name = bs_obj.attrs['aria-label'].replace('  ', ' ').strip().lower()
            sel_obj_name = obj.accessible_name.replace('  ', ' ').strip().lower()
            if bs_obj_name == sel_obj_name:
                return obj
        raise Exception(
            'Error finding selenium obj from BS obj: multiple objs found from class, could not disambiguate with accessible_name')
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
    buttons_dict = dict()
    for li_item in parent_ul.children:
        if set(li_item.next.attrs['class']) == sport_name_class_set:
            # This li_item is the name of a new sport
            cur_sport = str(list(li_item.descendants)[-1])
            cur_sport = ' '.join([x for x in cur_sport.split(' ') if x.lower() != 'live']).lower()
            if cur_sport not in games_dict:  # Check if the sport is already a key in games_dict
                games_dict[cur_sport] = []  # If not, create an empty list for it
        else:
            if li_item in list_parents:
                accessible_divs = li_item.find_all('div', attrs={"aria-label": True, "aria-hidden": False})
                accessible_spans = li_item.find_all('span', attrs={"aria-label": True, "aria-hidden": False})

                cur_relevant_buttons = [x for x in accessible_divs if is_relevant_button_alttxt(x)]
                cur_relevant_labels = [x for x in accessible_spans if any(
                    x.attrs['aria-label'] in s for s in [x.attrs['aria-label'] for x in cur_relevant_buttons])]

                if len(cur_relevant_buttons) != len(cur_relevant_labels):
                    raise Exception(f'Mismatch when parsing. Got a different number of button and label elements. '
                                    f'Buttons: \n{cur_relevant_buttons}\nLabels: \n{cur_relevant_labels}')

                odds_list = []
                cur_game_dict = dict()
                for i in range(len(cur_relevant_buttons)):
                    button = cur_relevant_buttons[i]
                    odds = None if 'aria-disabled' in button.attrs else str(list(button.descendants)[-1])
                    if odds is not None and len(odds) > 6:
                        odds = str(list(button.next.descendants)[-1])
                    odds_list.append(odds)

                    team_name = cur_relevant_labels[i].attrs['aria-label']
                    cur_game_dict[team_name] = odds_list[i]
                    buttons_dict[team_name] = button
                games_dict[cur_sport].append(cur_game_dict)
    return games_dict, buttons_dict


class FanduelController:
    def __init__(self, target_sport):
        self.driver = None
        self.target_sport = target_sport
        self.games_dict = None
        self.buttons_dict = None
        self.bookie_site_enum = BookieSite.FANDUEL

    def startup(self):
        self.driver = get_driver()

        self.driver.get('https://co.sportsbook.fanduel.com/live')

        # Click over to the tab for the target sport
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        buttons = soup.findAll('div', {'role': 'button'})
        sport_button = [x for x in buttons if 'aria-label' in x.attrs.keys() and self.target_sport.lower()
                        in x.attrs['aria-label'].lower()][0]
        sport_button = beautifulsoup_obj_to_selenium(sport_button, self.driver)
        sport_button.click()

        # Wait until the loading dots are no longer present in the DOM
        WebDriverWait(self.driver, 10).until_not(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//span[contains(@style, 'background-color: rgb(0, 95, 200);')]"))
        )

        print(f'Completed startup.')

    def place_bet(self, team_name, expected_moneyline, bet_amount):
        bet_button_bs = self.buttons_dict[team_name]

        css_selector = '.' + '.'.join(bet_button_bs.attrs['class'])
        sel_objs = self.driver.find_elements(By.CSS_SELECTOR, css_selector)

        bet_button_sel = None
        for obj in sel_objs:
            try:
                if team_name in str(obj.accessible_name):
                    bet_button_sel = obj
                    break
            except:
                pass
        if bet_button_sel is None:
            print(f'NOT PLACING BET because cannot find matching bet button for {team_name}')
            return False

        actual_odds = bet_button_sel.text
        if expected_moneyline != actual_odds:
            print(f'NOT PLACING BET because mismatch of odds: expected {expected_moneyline} but is now {actual_odds}')
            return False
        bet_button_sel.click()
        time.sleep(1)

        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        wager_input_tag = [x for x in soup.findAll('input', {'type': 'text'})
                           if x.parent.parent.next.next == 'WAGER'][0]
        css_selector = '.' + '.'.join(wager_input_tag.attrs['class'])
        sel_objs = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
        input_obj_selenium = [x for x in sel_objs if 'wager' in x.accessible_name.lower()][0]
        input_obj_selenium.send_keys(str(bet_amount))

        bottom_section_div = [x for x in wager_input_tag.find_parent('ul').parent.parent.children][-1]
        submit_button_bs = bottom_section_div.find_all('div', {'role': 'button'})[-1]

        css_selector = '.' + '.'.join(submit_button_bs.attrs['class'])
        sel_objs = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
        submit_button_sel = sel_objs[0]

        if 'log in' in submit_button_sel.accessible_name.lower():
            print(f'NOT PLACING BET because not logged in.')
            return False
        # TODO implement clicking the bet button and anything that happens after that
        # return True
        return False

    def run_main_loop(self, shared_dict, event, bet_dict):
        while True:
            if event.is_set():
                # If the event is set, place a bet
                bet_details = bet_dict[self.bookie_site_enum]
                bet_details = json.loads(bet_details)

                success = False
                try:
                    success = self.place_bet(team_name=bet_details['team_name'],
                                             expected_moneyline=bet_details['expected_moneyline'],
                                             bet_amount=bet_details['bet_amount'])
                except Exception as e:
                    pass

                if success:
                    event.clear()

            start_time = time.time()
            try:
                games_dict, buttons_dict = parse_page(self.driver)

                if games_dict is not None:
                    self.games_dict = games_dict
                    self.buttons_dict = buttons_dict
                    shared_dict[self.bookie_site_enum] = json.dumps(games_dict)
                    print(f'parsed page in {round(time.time() - start_time, 3)}s. games_dict: \n{games_dict}')

                    # TODO the following block of code tests placing a bet of $10 on the first valid bet on the page
                    # amount = 10
                    # valid_team_key = list(games_dict[self.target_sport][[None not in g.values() for g in games_dict[self.target_sport]].index(True)].keys())[0]
                    # team_key_idx = [i for i, x in enumerate(games_dict[self.target_sport]) if valid_team_key in x][0]
                    # expected_moneyline = games_dict[self.target_sport][team_key_idx][valid_team_key]
                    # did_place_bet = self.place_bet(valid_team_key, expected_moneyline, amount)

            except Exception as e:
                print(f'!!! Got exception after {round(time.time() - start_time, 3)}s: {e}')
            x = 1


if __name__ == '__main__':
    controller = FanduelController(target_sport='baseball')
    controller.startup()
    controller.run_main_loop()
