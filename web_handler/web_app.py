from flask import Flask, render_template

from shared_tools.logger import log

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/movies/')
def movies():
    return render_template('movies.html')


def run_webapp():
    log(msg="Web App Starting")
    app.run(host="0.0.0.0", debug=True)
