import logging
import pandas as pd
import os
import wb6ndjenvironment.process_messages

from flask import Flask, render_template, jsonify

DEFAULT_LEVEL = logging.INFO
FORMATTER = logging.Formatter(
    "%(asctime)s|%(process)d|%(module)s|%(levelname)s|%(message)s"
)
LOGGER = logging.getLogger()
LOGGER.setLevel(DEFAULT_LEVEL)


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/data/temperature_inside')
def temperature_inside():
    data = pd.read_csv("wb6ndjenvironment/TEMPERATURE_INSIDE.txt")
    columns = [data["DATE"].tolist(), data["VALUE"].tolist()]
    return jsonify(data=columns)


@app.route('/data/humidity_inside')
def humidity_inside():
    data = pd.read_csv("wb6ndjenvironment/HUMIDITY_INSIDE.txt")
    columns = [data["DATE"].tolist(), data["VALUE"].tolist()]
    return jsonify(data=columns)


if __name__ == '__main__':
    if "PORT" in os.environ:
        app.run(debug=True, port=os.environ["PORT"])
    else:
        app.run(debug=True)
