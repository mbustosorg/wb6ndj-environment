import wb6ndjenvironment
import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
import pandas as pd
from flask import Flask, render_template, jsonify

load_dotenv()

sql_engine = create_engine(
    f"mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}/{os.environ['DB']}",
    pool_recycle=3600, isolation_level="AUTOCOMMIT")

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/data/temperature_inside')
def temperature_inside():
    try:
        db_connection = sql_engine.connect()
        data = pd.read_sql("select * from wb6ndjenv.TEMPERATURE_INSIDE", db_connection)
        db_connection.close()
        columns = [data["date"].tolist(), data["TEMPERATURE_INSIDE"].tolist()]
        return jsonify(data=columns)
    except:
        db_connection.rollback()
        db_connection.close()


@app.route('/data/humidity_inside')
def humidity_inside():
    try:
        db_connection = sql_engine.connect()
        data = pd.read_sql("select * from wb6ndjenv.HUMIDITY_INSIDE", db_connection)
        db_connection.close()
        columns = [data["date"].tolist(), data["HUMIDITY_INSIDE"].tolist()]
        return jsonify(data=columns)
    except:
        db_connection.rollback()
        db_connection.close()


if __name__ == '__main__':
    if "PORT" in os.environ:
        app.run(debug=True, port=os.environ["PORT"])
    else:
        app.run(debug=True)
