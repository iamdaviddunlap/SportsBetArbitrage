import requests
import json

if __name__ == '__main__':
    api_key = '8bfeb68567d6280c66a8678d5ac6ac89'
    base_url = f'https://api.the-odds-api.com'
    all_sports_url = f'{base_url}/v4/sports/?apiKey={api_key}'

    res = requests.get(all_sports_url)
    res_json = res.json()
    print(f'Getting data for {len(res_json)} sports...')


    okay_sports = []
    bad_sports = []
    sports_info = {}

    for sport_json in res_json:
        sport_key = sport_json['key']
        specific_sport_url = f'{base_url}/v4/sports/{sport_key}/odds?regions=us&markets=h2h&oddsFormat=decimal&apiKey={api_key}'
        res = requests.get(specific_sport_url)
        games_json = res.json()
        if res.status_code == 200:
            for game_json in games_json:
                for bookmaker in game_json['bookmakers']:
                    for market in bookmaker['markets']:
                        if len(market['outcomes']) != 2:
                            if sport_key not in bad_sports:
                                bad_sports.append(sport_key)
                            break
                        else:
                            if sport_key not in okay_sports:
                                okay_sports.append(sport_key)
        elif res.status_code == 422:
            pass
        else:
            raise Exception(f'Unexpected status code {res.status_code} for {sport_key}')

    sports_json = {x['key']: x['title'] for x in res_json if x['key'] in okay_sports}
    print('Updating sports.json...')
    with open('sports.json', 'w') as f:
        f.write(json.dumps(sports_json, indent=4))

    print('Updating config.json...')
    with open('config.json', 'r+') as f:
        config = json.loads(f.read())
        f.seek(0)
        config['possible_sports'] = okay_sports
        f.write(json.dumps(config, indent=4))
        f.truncate()

    print(f'Okay sports (ones that only have 2 outcomes): {okay_sports}')
    print(f'Bad sports (ones in the API, but have more than 2 outcomes (e.g. Draw)): {bad_sports}')
