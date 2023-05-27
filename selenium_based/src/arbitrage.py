import json
import time

from util import BookieSite


def us_to_eu(us_odds):
    if us_odds[0] == '+':
        us_odds = int(us_odds[1:])
        eu_odds = (us_odds / 100) + 1
        return eu_odds
    elif us_odds[0] == '-' or us_odds[0] == '−':
        us_odds = int(us_odds[1:])
        eu_odds = (1 / (us_odds / 100)) + 1
        return eu_odds
    else:
        raise Exception(f'Unexpected first character in US odds: {us_odds}')


def eu_to_percent(eu_odds):
    return round((1 / eu_odds) * 100, 4)


def find_arbitrage(games_dict):
    """
    Given a games_dict that contains info about many bookie sites, this function will search for any arbitrages.
    :param games_dict: A dict whose keys are BookieSites and values are created by each of the various controllers
    :return: List of tuples representing bets that should be placed for arbitrages that were found. The list contains
    tuples of length 2 representing the 2 bets that should be placed. Each item is another tuple in the format:
    (BookieSite, team_name, expected_odds). An example list that may be returned is:
    [((BookieSite.DRAFTKINGS, 'kia tigers', '-111'), (BookieSite.FANDUEL, 'lg twins', '+125'))]
    """
    bookie_sites = list(games_dict.keys())
    all_sports = set([item for sublist in games_dict.values() for item in sublist])
    all_arb_bets = []
    for sport in all_sports:
        bookie_games_dict = {}
        bookie_games_set_dict = {}
        for bookie_site in bookie_sites:
            if bookie_site == BookieSite.FANDUEL:
                games_lst = games_dict[bookie_site][sport]
            elif bookie_site == BookieSite.DRAFTKINGS:
                games_lst = [item for sublist in [x for x in games_dict[BookieSite.DRAFTKINGS][sport].values()] for item in sublist]
            bookie_games_dict[bookie_site] = games_lst
            bookie_games_set_dict[bookie_site] = [set(y.lower() for y in x.keys()) for x in games_lst]

        games_sets_with_dups = [item for sublist in [v for v in bookie_games_set_dict.values()] for item in sublist]
        unique_games_sets = list(set(frozenset(item) for item in games_sets_with_dups))
        for game_set in unique_games_sets:
            # Get dict of BookieSite to the singular game_dict for this game_set
            # Only BookieSites that have odds this game will be in the dict
            all_odds_for_game = {k: [set([z.lower() for z in y.keys()]) == game_set for y in v] for k, v in bookie_games_dict.items()}
            all_odds_for_game = {k: None if True not in v else bookie_games_dict[k][v.index(True)] for k, v in all_odds_for_game.items()}
            all_odds_for_game = {k: v for k, v in all_odds_for_game.items() if v is not None and any(v.values())}
            if len(all_odds_for_game) >= 2:
                # Only look for an arbitrage if we have odds for this game on 2 or more sites
                teams = list(game_set)
                odds_for_teams_us = {t: [[(k, v) for k2, v in team_dict.items() if t.lower() == k2.lower()][0] for k, team_dict in all_odds_for_game.items()] for t in teams}
                odds_for_teams_eu = {k: [(bookie, eu_to_percent(us_to_eu(odds))) for bookie, odds in v] for k, v in odds_for_teams_us.items()}

                for bookie0, odds0 in odds_for_teams_eu[teams[0]]:
                    for bookie1, odds1 in odds_for_teams_eu[teams[1]]:
                        odds_sum = (odds0 + odds1)
                        if odds_sum < 99:
                            us_odds_0 = [x[1] for x in odds_for_teams_us[teams[0]] if x[0] == bookie0][0]
                            us_odds_1 = [x[1] for x in odds_for_teams_us[teams[1]] if x[0] == bookie1][0]
                            print(f'Should bet on "{teams[0]}" with {bookie0} (us: {us_odds_0}, eu: {odds0}), and on "{teams[1]}" with {bookie1} (us: {us_odds_1}, eu: {odds1}) for total odds of {odds_sum}')
                            bet0 = (bookie0, teams[0], us_odds_0)
                            bet1 = (bookie1, teams[1], us_odds_1)
                            all_arb_bets.append((bet0, bet1))
    return all_arb_bets


if __name__ == '__main__':
    mental_model = json.loads('{"BookieSite.FANDUEL":{"baseball":[{"LG Twins":"+125","Kia Tigers":"-154"},{"Lotte Giants":null,"Kiwoom Heroes":null},{"Hanwha Eagles":"-8000","NC Dinos":null},{"Hokkaido Nippon-Ham Fighters":"-2400","Tohoku Rakuten Golden Eagles":"+1100"},{"Yokohama Dena Baystars":"-124","Chunichi Dragons":"-102"},{"Chiba Lotte Marines":null,"Fukuoka Softbank Hawks":null},{"Yomiuri Giants":null,"Hanshin Tigers":null}]},"BookieSite.DRAFTKINGS":{"baseball":{"KBO":[{"LG Twins":"-110","KIA Tigers":"-111"},{"Hanwha Eagles":null,"NC Dinos":null},{"Lotte Giants":null,"Kiwoom Heroes":null}],"NPB":[{"Hokkaido Nippon Ham Fighters":"-1600","Tohoku Rakuten Golden Eagles":"+850"},{"Chiba Lotte Marines":null,"Fukuoka Softbank Hawks":null},{"Yomiuri Giants":null,"Hanshin Tigers":null},{"Yokohama DeNA BayStars":"-125","Chunichi Dragons":"-105"}]}}}')
    mental_model = {eval(k): v for k, v in mental_model.items()}
    start = time.perf_counter()
    all_arb_bets = find_arbitrage(mental_model)
    print(all_arb_bets)
    print(f'Finished v1 in {time.perf_counter() - start}s')
