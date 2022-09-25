from flask import Flask, render_template, request, redirect
import json

from arbitrage import find_arbs


app = Flask(__name__)

with open('../config.json') as f:
    config = json.loads(f.read())
with open('../sports.json') as f:
    sports_info = json.loads(f.read())

# TODO maybe write function to validate the config to make sure all elements of approved_sports are in sports_info.keys

params = {
    'api_key': '',
    'update_freq': 30,
    'total_bet': 100,
    'rounding_dollars': 5,
    'approved_sports': config['approved_sports'],
    'sports_to_check': config['approved_sports'],
    'sports_info': sports_info
}


@app.route("/")
def main():
    return render_template('index.html', **params)


@app.route("/submit-api-info")
def form_submit():
    args = request.args
    params['api_key'] = args['apikey']
    params['update_freq'] = args['update-freq']

    new_sports_to_check = []
    for sport_key in params['approved_sports']:
        if sport_key in args:
            new_sports_to_check.append(sport_key)
    params['sports_to_check'] = new_sports_to_check

    return redirect('/')


@app.route("/query-arbitrage")
def query_arbitrage():
    arb_obj, remaining_requests = find_arbs(params['api_key'], config['approved_bookmakers'], params['sports_to_check'],
                                            params['total_bet'], params['rounding_dollars'], sports_info)
    return {'arb_obj': arb_obj, 'remaining_requests': remaining_requests}


if __name__ == "__main__":
    app.run()
