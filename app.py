"""Flask application to server website for environmental data"""
import dateutil.parser
import datetime
import os
from zoneinfo import ZoneInfo

import pandas as pd
import numpy as np
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
        start_date = pd.Timestamp.now(tz="UTC") + datetime.timedelta(days=-3)
        db_connection = sql_engine.connect()
        data = pd.read_sql(f"select * from wb6ndjenv.{sensor} order by \"date\"", db_connection)
        db_connection.close()
        data["date"] = data["date"].apply(lambda x: pd.Timestamp(dateutil.parser.isoparse(x + "Z")))
        data = data[data["date"] >= start_date]
        data["date"] = data["date"].apply(lambda x: x.astimezone(ZoneInfo("America/Los_Angeles")))
        data["name"] = sensor
        data = data.rename(columns={sensor: "tempXS"})
        #columns = [data["date"].tolist(), data[sensor].tolist()]
        return data#jsonify(data=columns)
    except:
        db_connection.rollback()
        db_connection.close()


@app.route("/data/<sensor_name>")
def sensor_value(sensor_name: str):
    """Endpoint for sensor data"""
    return data_for_sensor(sensor_name.upper())


def sensor_values(sensor_type: str):
    """Endpoint for sensor data"""
    inside = data_for_sensor(f"{sensor_type}_INSIDE")
    inside["tempXS"] = inside["tempXS"].astype(float)
    outside = data_for_sensor(f"{sensor_type}_OUTSIDE")
    outside["tempXS"] = outside["tempXS"].astype(float)
    repeater = data_for_sensor(f"{sensor_type}_REPEATER")
    repeater["tempXS"] = repeater["tempXS"].astype(float)
    if not inside.shape[0]:
        first = outside
        first = first.rename(columns={"tempXS": f"{sensor_type}_OUTSIDE"})
        first = first.drop(["name"], axis=1)
        first[f"{sensor_type}_INSIDE"] = np.nan
    elif not outside.shape[0]:
        first = inside
        first = first.rename(columns={"tempXS": f"{sensor_type}_INSIDE"})
        first = first.drop(["name"], axis=1)
        first[f"{sensor_type}_OUTSIDE"] = np.nan
    elif inside["date"].iloc[-1] > outside["date"].iloc[-1]:
        first = pd.merge_ordered(inside, outside, on="date") #, tolerance=pd.Timedelta("1d"))
        first = first.rename(columns={"tempXS_x": f"{sensor_type}_INSIDE", "tempXS_y": f"{sensor_type}_OUTSIDE"})
    else:
        first = pd.merge_ordered(outside, inside, on="date") #, tolerance=pd.Timedelta("1d"))
        first = first.rename(columns={"tempXS_x": f"{sensor_type}_OUTSIDE", "tempXS_y": f"{sensor_type}_INSIDE"})
    if not repeater.shape[0]:
        second = first
        second[f"{sensor_type}_REPEATER"] = np.nan
    elif first["date"].iloc[-1] > repeater["date"].iloc[-1]:
        second = pd.merge_ordered(first, repeater, on="date") #, tolerance=pd.Timedelta("1d"))
        second = second.rename(columns={"tempXS": f"{sensor_type}_REPEATER"})
        second = second.drop(["name_x", "name_y", "name"], axis=1)
    else:
        second = pd.merge_ordered(repeater, first, on="date") #, tolerance=pd.Timedelta("1d"))
        second = second.rename(columns={"tempXS": f"{sensor_type}_REPEATER"})
        second = second.drop(["name_x", "name_y", "name"], axis=1)

    fan_state = data_for_sensor("FAN_STATE")
    fan_state["tempXS"] = fan_state["tempXS"].apply(lambda x: float(x) * 10.0 + 30.0)

    second = pd.merge_asof(second, fan_state, on="date", tolerance=pd.Timedelta("2d"))
    second = second.rename(columns={"tempXS": "FAN_STATE"})
    second = second.drop(["name"], axis=1)
    second = second.set_index(["date"], drop=False)
    second[f"{sensor_type}_INSIDE"] = second[[f"{sensor_type}_INSIDE"]].interpolate(method="time")
    second[f"{sensor_type}_OUTSIDE"] = second[[f"{sensor_type}_OUTSIDE"]].interpolate(method="time")
    second[f"{sensor_type}_REPEATER"] = second[[f"{sensor_type}_REPEATER"]].interpolate(method="time")
    second = second.replace(float("nan"), "nan")

    columns = [second["date"].tolist(), second[f"{sensor_type}_INSIDE"].tolist(), second[f"{sensor_type}_REPEATER"].tolist(), second[f"{sensor_type}_OUTSIDE"].tolist(), second["FAN_STATE"].tolist()]
    return jsonify(data=columns)


@app.route("/data/temperature")
def temperature_values():
    """Endpoint for temperature sensor data"""
    return sensor_values("TEMPERATURE")


@app.route("/data/humidity")
def humidity_values():
    """Endpoint for humidity sensor data"""
    return sensor_values("HUMIDITY")

@app.route("/data/fan_state")
def fan_state():
    """Endpoint for fan state"""
    try:
        start_date = pd.Timestamp.now(tz="UTC") + datetime.timedelta(days=-3)
        db_connection = sql_engine.connect()
        data = pd.read_sql(f"select * from wb6ndjenv.FAN_STATE order by `date` desc", db_connection)
        db_connection.close()
        data["date"] = data["date"].apply(lambda x: pd.Timestamp(dateutil.parser.isoparse(x + "Z")))
        data = data[data["date"] >= start_date]
        data["date"] = data["date"].apply(lambda x: x.astimezone(ZoneInfo("America/Los_Angeles")))
        return jsonify(data=[data["date"].tolist(), data["FAN_STATE"].tolist()])
    except:
        db_connection.rollback()
        db_connection.close()


if __name__ == "__main__":
    if "PORT" in os.environ:
        app.run(debug=True, port=os.environ["PORT"])
    else:
        app.run(debug=True)
