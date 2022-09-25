import requests


def find_arbs(api_key, sports, total_bet, rounding_dollars):

    output_obj = []

    for sport in sports:

        base_url = f'https://api.the-odds-api.com'
        specific_sport_url = f'{base_url}/v4/sports/{sport}/odds?regions=us&markets=h2h&oddsFormat=decimal&apiKey={api_key}'
        res = requests.get(specific_sport_url)
        games_json = res.json()

        remaining_requests = int(res.headers['x-requests-remaining'])

        sport_title = games_json[0]["sport_title"]
        print(f'Analyzing {sport_title}...')

        sport_obj = {
            'sport_title': sport_title,
            'sport_id': games_json[0]["sport_key"],
            'arb_games': []
        }

        # approved_bookmakers = ['barstool', 'betfair', 'betmgm', 'betonlineag', 'betrivers', 'betus', 'bovada', 'draftkings', 'fanduel', 'gtbets', 'intertops', 'lowvig', 'mybookieag', 'pointsbetus', 'sugarhouse', 'superbook', 'unibet', 'williamhill_us', 'wynnbet']
        approved_bookmakers = ['draftkings', 'fanduel', 'barstool', 'betrivers', 'bovada']

        for game_json in games_json:
            home_team_odds = {}
            away_team_odds = {}
            for bookmaker in game_json['bookmakers']:
                if bookmaker['key'] in approved_bookmakers:
                    for market in bookmaker['markets']:

                        if market['key'] not in ['h2h', 'h2h_lay', 'outrights', 'outrights_lay']:
                            print(f'Found unexpected market: {market["key"]}')

                        if market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                odds = (1 / outcome['price']) * 100
                                if outcome['name'] == game_json['home_team']:
                                    # These are the odds for the home team
                                    home_team_odds[bookmaker['title']] = odds
                                elif outcome['name'] == game_json['away_team']:
                                    # These are the odds for the away team
                                    away_team_odds[bookmaker['title']] = odds
                                else:
                                    print(f'Found neither away nor home! Name: {outcome["name"]}')

            found_arb = False
            best_arb = None
            best_arb_worst_case = -100
            for home_bookmaker in home_team_odds.keys():
                for away_bookmaker in away_team_odds.keys():

                    home_odds = home_team_odds[home_bookmaker]
                    away_odds = away_team_odds[away_bookmaker]
                    total = home_odds + away_odds
                    if total < 99.5 and home_odds > 5 and away_odds > 5:
                        found_arb = True

                        # Calculate investment amounts
                        # TODO want to round these before actually investing
                        # total_bet = 100
                        # rounding_dollars = 1

                        home_bet = (total_bet * home_odds) / total
                        away_bet = (total_bet * away_odds) / total

                        # Round the bets
                        home_bet = round(home_bet / rounding_dollars) * rounding_dollars
                        away_bet = round(away_bet / rounding_dollars) * rounding_dollars

                        home_win_payout = home_bet * (100 / home_odds)
                        away_win_payout = away_bet * (100 / away_odds)

                        avg_home_odds = ((home_odds + (100 - away_odds)) / 2) / 100
                        avg_away_odds = 1 - avg_home_odds

                        expected_payout = (home_win_payout * avg_home_odds) + (away_win_payout * avg_away_odds)
                        expected_profit = expected_payout - total_bet
                        expected_profit = round(expected_profit, 2)

                        worst_case_profit = min(home_win_payout, away_win_payout) - total_bet
                        worst_case_profit = round(worst_case_profit, 2)

                        if worst_case_profit < 0:
                            x = 1

                        eu_home_odds = round(100 / home_odds, 2)
                        eu_away_odds = round(100 / away_odds, 2)
                        us_home_odds = round(100 * (eu_home_odds - 1)) if eu_home_odds >= 2.0 else round(
                            -100 / (eu_home_odds - 1))
                        us_away_odds = round(100 * (eu_away_odds - 1)) if eu_away_odds >= 2.0 else round(
                            -100 / (eu_away_odds - 1))

                        if worst_case_profit > best_arb_worst_case:
                            best_arb_worst_case = worst_case_profit
                            best_arb = [{'team': game_json["home_team"], 'bookmaker': home_bookmaker, 'bet': home_bet,
                                         'eu_odds': eu_home_odds, 'us_odds': us_home_odds},
                                        {'team': game_json["away_team"], 'bookmaker': away_bookmaker, 'bet': away_bet,
                                         'eu_odds': eu_away_odds, 'us_odds': us_away_odds},
                                        {'investment': total_bet, 'expected': expected_profit,
                                         'worst': worst_case_profit}]
            if found_arb:
                home_stats = best_arb[0]
                away_stats = best_arb[1]
                money_stats = best_arb[2]
                print(
                    f'Found arbitrage! Game: {home_stats["team"]} ({home_stats["eu_odds"]} / {home_stats["us_odds"]}) vs {away_stats["team"]} ({away_stats["eu_odds"]} / {away_stats["us_odds"]}), '
                    f'Home bookmaker: {home_stats["bookmaker"]} (${home_stats["bet"]}), Away bookmaker: {away_stats["bookmaker"]} (${away_stats["bet"]}), '
                    f'expected profit (${money_stats["investment"]} investment): ${money_stats["expected"]}, '
                    f'worst case profit: ${money_stats["worst"]}')
                game_obj = {
                    'home': home_stats["team"],
                    'away': away_stats["team"],
                    'expected_profit': money_stats["expected"],
                    'worst_case_profit': money_stats["worst"],
                    'home_bookmaker': {
                        'name': home_stats["bookmaker"],
                        'odds_eu': home_stats["eu_odds"],
                        'odds_us': home_stats["us_odds"],
                        'bet': home_stats["bet"]
                    },
                    'away_bookmaker': {
                        'name': away_stats["bookmaker"],
                        'odds_eu': away_stats["eu_odds"],
                        'odds_us': away_stats["us_odds"],
                        'bet': away_stats["bet"]
                    },
                }
                sport_obj['arb_games'].append(game_obj)
        sport_obj['arb_games'] = sorted(sport_obj['arb_games'], key=lambda x: x['worst_case_profit'], reverse=True)
        output_obj.append(sport_obj)
    return output_obj


if __name__ == '__main__':
    api_key = 'aba9be41bd7166af142232eca6e1e960'

    approved_sports = ['americanfootball_cfl', 'americanfootball_ncaaf', 'americanfootball_nfl', 'baseball_mlb',
                       'basketball_nba', 'cricket_caribbean_premier_league', 'cricket_icc_world_cup',
                       'cricket_international_t20', 'icehockey_nhl', 'mma_mixed_martial_arts']
    # approved_sports = ['americanfootball_cfl', 'americanfootball_ncaaf', 'americanfootball_nfl', 'baseball_mlb', 'basketball_nba', 'icehockey_nhl']

    res = find_arbs(api_key, approved_sports, total_bet=100, rounding_dollars=1)

    x = 1

# a = [
#
#     {
#         'sport': 'NBA',
#         'arb_games': [
#             {
#                 'home': ' South Alabama Jaguars',
#                 'away': 'Louisiana Tech Bulldogs',
#                 'expected_profit': '8.83',
#                 'worst_case_profit': '4.0',
#                 'home_bookmaker': {
#                     'name': 'fanduel',
#                     'odds_eu': '1.19',
#                     'odds_us': '-526',
#                     'bet': '92'
#                 },
#                 'away_bookmaker': {
#                     'name': 'draftkings',
#                     'odds_eu': '13.0',
#                     'odds_us': '1200',
#                     'bet': '8'
#                 }
#             }
#         ]
#     },
#
# ]
