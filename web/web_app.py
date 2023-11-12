from flask import Flask, render_template
import logger

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html', log_path='../log/log-' + logger.today_date + '.log')


@app.route('/movies/')
def movies():
    return render_template('movies.html')
