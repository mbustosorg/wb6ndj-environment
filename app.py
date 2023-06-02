"""Flask application to server website for environmental data"""
import dateutil.parser
import os
from zoneinfo import ZoneInfo

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
from sqlalchemy import create_engine

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
        data = pd.read_sql(f"select * from wb6ndjenv.{sensor} order by \"date\"", db_connection)
        db_connection.close()
        data["date"] = data["date"].apply(lambda x: dateutil.parser.isoparse(x + "Z").astimezone(ZoneInfo("America/Los_Angeles")))
        columns = [data["date"].tolist(), data[sensor].tolist()]
        return jsonify(data=columns)
    except:
        db_connection.rollback()
        db_connection.close()


@app.route("/data/<sensor_name>")
def sensor_value(sensor_name: str):
    """Endpoint for sensor data"""
    return data_for_sensor(sensor_name.upper())


@app.route("/data/fan_state")
def fan_state():
    """Endpoint for fan state"""
    fan_state = data_for_sensor("FAN_STATE")
    return fan_state["FAN_STATE"][-1]


if __name__ == "__main__":
    if "PORT" in os.environ:
        app.run(debug=True, port=os.environ["PORT"])
    else:
        app.run(debug=True)
