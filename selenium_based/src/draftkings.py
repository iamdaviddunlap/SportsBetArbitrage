import time
from bs4 import BeautifulSoup
import json

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from util import get_driver, BookieSite


def expand_accordions(driver):
    accordions = []
    num_loops = 0
    while len(accordions) == 0:
        num_loops += 1
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        accordions = list(soup.find_all('div', {'class': 'sportsbook-accordion__accordion'}))
        if len(accordions) == 0 and num_loops >= 100:
            raise Exception(f'Have looped for {num_loops} tries, and there\'s still no accordions')
        time.sleep(0.5)

    if 'false' in [x.attrs['aria-expanded'] for x in accordions]:
        print('There are unexpanded accordions, so we\'re clicking them...')
        divs = driver.find_elements(By.XPATH, "//div[contains(@class, 'sportsbook-accordion__accordion') "
                                              "and @role='button' "
                                              "and @aria-expanded='false']")
        for div in divs: div.click()
        return True
    return False


def set_sport(driver, target_sport):
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    cur_sport_a_tag = soup.find('a', {'class': 'sportsbook-tabbed-subheader__tab-link', 'aria-selected': 'true'})
    cur_sport = [x for x in cur_sport_a_tag.descendants][-1].lower()
    if cur_sport != target_sport:
        target_sport_a_tag = next((element for element in
                                   driver.find_elements(By.XPATH,
                                                        "//a[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'basketball') "
                                                        "and contains(@class, 'sportsbook-tabbed-subheader__tab-link')]"
                                                        )), None)
        print(f'You are not on the page for the target sport, clicking link for {target_sport} page...')
        target_sport_a_tag.click()
        return True
    return False


def parse_page(driver):
    accordion_divs = []
    table_bodies = []
    num_loops = 0
    while len(table_bodies) == 0 or None in table_bodies:
        num_loops += 1
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        accordion_divs = list(soup.find_all('div', {'class': 'sportsbook-accordion__wrapper'}))
        table_bodies = [x.find('tbody', {'class': 'sportsbook-table__body'}) for x in accordion_divs]
        if len(table_bodies) == 0 or None in table_bodies:
            if num_loops >= 100:
                raise Exception(f'Have looped for {num_loops} tries, and there\'s still no loaded accordions')
            time.sleep(0.5)

    table_heads = [[y for y in x.find_all('thead', {'class': 'sportsbook-table__head'})][0] for x in accordion_divs]
    league_names = [str(list([y for y in x.find_all('div', {'class': 'sportsbook-header__title'})][0].descendants)[-1])
                    for x in accordion_divs]
    if len(league_names) != len(table_heads) or len(league_names) != len(table_bodies):
        raise Exception(f'Got a mismatch between elements. # table_heads: {len(table_heads)}, '
                        f'# league_names: {len(league_names)}, # table_bodies: {len(table_bodies)}')

    games_dict = {}
    buttons_dict = {}
    cur_matchup = None

    for i in range(len(table_heads)):
        table_head = table_heads[i]
        league_name = league_names[i]
        table_body = table_bodies[i]

        thead_labels = [str([x for x in th.descendants][-1]).lower() for th in table_head.find_all('th')]

        if 'moneyline' not in thead_labels:
            print(f"!! 'moneyline' not found in table_head labels, stopping parsing of {league_name} league")
            continue

        moneyline_idx = thead_labels.index('moneyline') - 1

        cur_sport_a_tag = soup.find('a', {'class': 'sportsbook-tabbed-subheader__tab-link', 'aria-selected': 'true'})
        cur_sport = [x for x in cur_sport_a_tag.descendants][-1].lower()
        if cur_sport not in games_dict:  # Check if the sport is already a key in games_dict
            games_dict[cur_sport] = dict()  # If not, create an empty dict for it
        if league_name not in games_dict[cur_sport].keys():
            games_dict[cur_sport][league_name] = []

        for tr in table_body.children:
            x = 1
            if 'break-line' in tr.attrs['class'] or cur_matchup is None:
                # This means that this tr is the start of a new match-up
                cur_matchup = {}
            team_name = str([x for x in tr.find('div', {'class': 'event-cell__name-text'}).descendants][-1])

            # Extract moneyline div from the page
            odds_tds = tr.find_all('td', {'class': 'sportsbook-table__column-row'})
            all_odds_divs_lsts = [x.find_all('div', {'class': 'sportsbook-outcome-cell__elements'}) for x in odds_tds]
            moneyline_divs_lst = all_odds_divs_lsts[moneyline_idx]
            moneyline_div = None if len(moneyline_divs_lst) == 0 else moneyline_divs_lst[0]

            if moneyline_div is not None:
                moneyline_button = odds_tds[moneyline_idx].find('div', {'role': 'button'})
                if team_name not in buttons_dict.keys():
                    buttons_dict[team_name] = moneyline_button

                moneyline_odds = str(list(moneyline_div.find('span').descendants)[-1])
                cur_matchup[team_name] = moneyline_odds
            else:
                cur_matchup[team_name] = None

            if len(cur_matchup) == 2:  # NOTE: we are assuming that all games are match-ups between 2 teams. This may not always be true, so watch out for that.
                games_dict[cur_sport][league_name].append(cur_matchup)
                cur_matchup = {}
    return games_dict, buttons_dict


class DraftKingsController:
    def __init__(self, target_sport):
        self.driver = None
        self.target_sport = target_sport
        self.games_dict = None
        self.buttons_dict = None
        self.bookie_site_enum = BookieSite.DRAFTKINGS

    def startup(self):
        self.driver = get_driver()

        self.driver.get('https://sportsbook.draftkings.com/live?category=live-in-game')

        # Set the sport to the target_sport if needed
        did_set_sport = set_sport(self.driver, self.target_sport)
        if did_set_sport: print('Successfully set the sport.')

        # Expand any accordions if needed
        did_expand_accordions = expand_accordions(self.driver)
        if did_expand_accordions: print('Successfully expanded the accordions.')

        print(f'Completed startup.')

    def place_bet(self, team_name, expected_moneyline, bet_amount):
        bet_button_bs = self.buttons_dict[team_name]

        sel_buttons = [x for x in self.driver.find_elements(By.XPATH,
                                                            f"//div[contains(@class, 'sportsbook-outcome-cell__body') "
                                                            f"and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{bet_button_bs.attrs['aria-label'].lower().strip()}') ]")]
        try:
            matching_button_idx = [x.text for x in sel_buttons].index(expected_moneyline)
            bet_button_sel = sel_buttons[matching_button_idx]
            res = bet_button_sel.click()
            time.sleep(1)
            if res is None:  # Trying to prevent error from
                wager_input = self.driver.find_element(By.XPATH,
                                                       f"//input[contains(@class, 'betslip-wager-box__input') "
                                                       f"and contains(@type, 'text')]")
                wager_input.send_keys(str(bet_amount))
                place_bet_button = self.driver.find_element(By.CLASS_NAME, "dk-place-bet-button__wrapper")
                if 'log in' in place_bet_button.text.lower():
                    print(f'NOT PLACING BET because not logged in.')
                    return False
                # TODO implement clicking the bet button and anything that happens after that
                x = 1
                return True
            else:
                print(f'Got unexpected result from clicking the bet_button: {res}')
                return False
        except ValueError as e:
            print(f'NOT PLACING BET because expected_moneyline ({expected_moneyline}) not found in button text: '
                  f'{[x.text for x in sel_buttons]}')
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
                    # valid_league_key = list(games_dict[self.target_sport].keys())[
                    #     [[None not in g.values() for g in games_lst].index(True)
                    #      for league, games_lst in games_dict[self.target_sport].items()][0]]
                    # valid_team_key = list(games_dict[self.target_sport][valid_league_key][0].keys())[0]
                    # expected_moneyline = games_dict[self.target_sport][valid_league_key][0][valid_team_key]
                    # did_place_bet = self.place_bet(valid_team_key, expected_moneyline, amount)

            except Exception as e:
                print(f'!!! Got exception after {round(time.time() - start_time, 3)}s: {e}')
            x = 1


if __name__ == '__main__':
    controller = DraftKingsController(target_sport='baseball')
    controller.startup()
    controller.run_main_loop()
