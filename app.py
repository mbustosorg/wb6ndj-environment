"""Flask application to server website for environmental data"""
import wb6ndjenvironment
import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
import pandas as pd
from flask import Flask, render_template, jsonify

load_dotenv()

sql_engine = create_engine(
    f"mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}/{os.environ['DB']}",
    pool_recycle=3600,
    isolation_level="AUTOCOMMIT",
)

app = Flask(__name__)


@app.route("/")
def index():
    """Index route"""
    return render_template("index.html")


def data_for_sensor(sensor: str):
    """Get data for 'sensor'"""
    try:
        db_connection = sql_engine.connect()
        data = pd.read_sql(f"select * from wb6ndjenv.{sensor}", db_connection)
        db_connection.close()
        columns = [data["date"].tolist(), data[sensor].tolist()]
        return jsonify(data=columns)
    except:
        db_connection.rollback()
        db_connection.close()


@app.route("/data/<sensor_name>")
def sensor_value(sensor_name: str):
    """Endpoint for sensor data"""
    return data_for_sensor(sensor_name.upper())


if __name__ == "__main__":
    if "PORT" in os.environ:
        app.run(debug=True, port=os.environ["PORT"])
    else:
        app.run(debug=True)
