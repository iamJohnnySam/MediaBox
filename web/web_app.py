from flask import Flask, render_template
from logging import logger

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html', log_path='../log/log-' + logger.today_date + '.log')


@app.route('/movies/')
def movies():
    return render_template('movies.html')


def run_webapp():
    if __name__ == '__main__':
        app.run(debug=False, host='0.0.0.0')
