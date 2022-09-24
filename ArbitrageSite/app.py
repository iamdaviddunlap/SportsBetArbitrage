from flask import Flask, render_template, request, redirect

app = Flask(__name__)

params = {
    'api_key': '',
    'update_freq': 30
}


@app.route("/")
def main():
    return render_template('index.html', api_key=params['api_key'], update_freq=params['update_freq'])


@app.route("/submit-api-info")
def form_submit():
    args = request.args
    params['api_key'] = args['apikey']
    params['update_freq'] = args['update-freq']
    return redirect('/')


if __name__ == "__main__":
    app.run()