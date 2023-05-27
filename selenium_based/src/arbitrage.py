import json
import time
import csv

from util import BookieSite, clean_str


def read_mlb_teams(csv_file_path='mlb_teams.csv'):
    teams = list()

    with open(csv_file_path, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            team_map = {k: v for k, v in zip(('long', 'short'), [clean_str(x) for x in row])}
            teams.append(team_map)
    return teams


def short_to_long(short_team, team_mappings):
    try:
        shorts = [x['short'] for x in team_mappings]
        res = [team_mappings[[x['short'] for x in team_mappings].index(word)]['long']
                for word in short_team.split(' ') if word in shorts][0]
        return res
    except Exception as e:
        return short_team


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


def get_unique_games(game_sets, team_mapping):
    unique_games = set()

    for game_set in game_sets:
        new_set = set()
        for item in game_set:
            new_set.add(short_to_long(item, team_mapping))
        unique_games.add(frozenset(new_set))

    return list(unique_games)


def find_arbitrage(games_dict):
    """
    Given a games_dict that contains info about many bookie sites, this function will search for any arbitrages.
    :param games_dict: A dict whose keys are BookieSites and values are created by each of the various controllers
    :return: List of tuples representing bets that should be placed for arbitrages that were found. The list contains
    tuples of length 2 representing the 2 bets that should be placed. Each item is another tuple in the format:
    (BookieSite, team_name, expected_odds). An example list that may be returned is:
    [((BookieSite.DRAFTKINGS, 'kia tigers', '-111'), (BookieSite.FANDUEL, 'lg twins', '+125'))]
    """

    # Extract all the bookie sites
    bookie_sites = list(games_dict.keys())

    # Collect all sports across all bookie sites into a set to remove duplicates
    all_sports = set([item for sublist in games_dict.values() for item in sublist])

    all_arb_bets = []

    for sport in all_sports:
        bookie_games_dict = {}
        bookie_games_set_dict = {}
        for bookie_site in bookie_sites:
            # Differentiate between FANDUEL and DRAFTKINGS to get the list of games
            if bookie_site == BookieSite.FANDUEL:
                games_lst = games_dict[bookie_site][sport]
            elif bookie_site == BookieSite.DRAFTKINGS:
                games_lst = [item for sublist in [x for x in games_dict[BookieSite.DRAFTKINGS][sport].values()]
                             for item in sublist]

            bookie_games_dict[bookie_site] = games_lst
            bookie_games_set_dict[bookie_site] = [set(clean_str(y) for y in x.keys()) for x in games_lst]

        games_sets_with_dups = [item for sublist in [v for v in bookie_games_set_dict.values()] for item in sublist]

        team_mapping = read_mlb_teams()
        unique_games_sets = get_unique_games(games_sets_with_dups, team_mapping)

        for game_set in unique_games_sets:
            # Preparing dicts to hold odds for the games
            all_odds_for_game = {}
            for bookie_site, bookie_games_list in bookie_games_dict.items():
                matching_games = []
                for game in bookie_games_list:
                    game_keys_set = set()
                    for team in game.keys():
                        game_keys_set.add(short_to_long(clean_str(team), team_mapping))
                    if game_keys_set == game_set:
                        matching_games.append(True)
                    else:
                        matching_games.append(False)
                all_odds_for_game[bookie_site] = matching_games

            all_odds_for_game_filtered = {}
            for bookie_site, bookie_games_list in all_odds_for_game.items():
                if True in bookie_games_list:
                    all_odds_for_game_filtered[bookie_site] = bookie_games_dict[bookie_site][bookie_games_list.index(True)]

            # Filter out games where the odds for a team are None
            all_odds_for_game_filtered = {k: v for k, v in all_odds_for_game_filtered.items() if
                                          v is not None and any(v.values())}

            # Check if we have odds from at least two sites
            if len(all_odds_for_game_filtered) >= 2:
                teams = list(game_set)
                odds_for_teams_us = {}
                odds_for_teams_eu = {}

                for team in teams:
                    odds_for_teams_us[team] = []
                    for bookie_site, team_dict in all_odds_for_game_filtered.items():
                        for bookie_team_name, bookie_games_list in team_dict.items():
                            if clean_str(team) == short_to_long(clean_str(bookie_team_name), team_mapping):
                                odds_for_teams_us[team].append((bookie_site, bookie_games_list))
                    odds_for_teams_eu[team] = [(bookie, eu_to_percent(us_to_eu(odds))) for bookie, odds in
                                               odds_for_teams_us[team]]

                for bookie0, odds0 in odds_for_teams_eu[teams[0]]:
                    for bookie1, odds1 in odds_for_teams_eu[teams[1]]:
                        odds_sum = (odds0 + odds1)

                        if odds_sum < 99:
                            us_odds_0 = [x[1] for x in odds_for_teams_us[teams[0]] if x[0] == bookie0][0]
                            us_odds_1 = [x[1] for x in odds_for_teams_us[teams[1]] if x[0] == bookie1][0]
                            print(f'Should bet on "{teams[0]}" with {bookie0} (us: {us_odds_0}, eu: {odds0}), '
                                  f'and on "{teams[1]}" with {bookie1} (us: {us_odds_1}, eu: {odds1}) '
                                  f'for total odds of {odds_sum}')

                            bet0 = (bookie0, teams[0], us_odds_0)
                            bet1 = (bookie1, teams[1], us_odds_1)
                            all_arb_bets.append((bet0, bet1))

    return all_arb_bets


if __name__ == '__main__':
    mental_model = json.loads('{"BookieSite.FANDUEL": {"baseball": [{"Texas Rangers": "-650", "Baltimore Orioles": "+390"}, {"Houston Astros": "-750", "Oakland Athletics": "+460"}, {"Philadelphia Phillies": "-430", "Atlanta Braves": "+300"}, {"San Francisco Giants": "-186", "Milwaukee Brewers": "+146"}, {"Washington Nationals": "+300", "Kansas City Royals": "-450"}, {"Pittsburgh Pirates": "+1500", "Seattle Mariners": "-3500"}, {"Los Angeles Dodgers": "+166", "Tampa Bay Rays": "-215"}, {"Florida Gators": "+680", "Vanderbilt Commodores": "-1800"}]}, "BookieSite.DRAFTKINGS": {"baseball": {"MLB": [{"TEX Rangers": "-570", "BAL Orioles": "+410"}, {"HOU Astros": "-425", "OAK Athletics": "+320"}, {"LA Dodgers": "+150", "TB Rays": "-185"}, {"PHI Phillies": "-425", "ATL Braves": "+320"}, {"SF Giants": "-195", "MIL Brewers": "+160"}, {"PIT Pirates": "+1200", "SEA Mariners": "-3000"}, {"WAS Nationals": "+290", "KC Royals": "-380"}]}}}')
    mental_model = {eval(k): v for k, v in mental_model.items()}
    start = time.perf_counter()
    all_arb_bets = find_arbitrage(mental_model)
    print(all_arb_bets)
    print(f'Finished v4 in {time.perf_counter() - start}s')
