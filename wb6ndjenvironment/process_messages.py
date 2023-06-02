"""Application to monitor MQTT messsages and store to a database"""
import datetime
import logging
import os
import time
from dotenv import load_dotenv

import pymysql
from sqlalchemy import create_engine
import pandas as pd
import paho.mqtt.client as mqtt

LOGGER = logging.getLogger()

load_dotenv()

broker_address = os.environ["BROKER_ADDRESS"]
broker_port = int(os.environ["BROKER_PORT"])
topics = ["TEMPERATURE_INSIDE", "HUMIDITY_INSIDE", "TEMPERATURE_REPEATER", "HUMIDITY_REPEATER", "TEMPERATURE_OUTSIDE", "HUMIDITY_OUTSIDE", "FAN_STATE"]


sql_engine = create_engine(
    f"mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}/{os.environ['DB']}",
    pool_recycle=3600,
)


def on_message(client, userdata, message):
    """Handle a message from the MQTT broker"""
    try:
        df = pd.DataFrame(
            [[datetime.datetime.utcnow().isoformat(), message.payload.decode()]],
            columns=["date", message.topic],
        )
        db_connection = sql_engine.connect()
        df.to_sql(message.topic, db_connection, if_exists="append", index=False)
        db_connection.close()
        LOGGER.info(
            f"Message received and saved to file {message.topic}:  {message.payload.decode()}"
        )
    except:
        db_connection.rollback()
        db_connection.close()


def mqtt_connect():
    """Connect and return client"""
    client = mqtt.Client()
    client.on_message = on_message
    client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
    client.username_pw_set(os.environ["MQTT_USERNAME"], os.environ["MQTT_PASSWORD"])
    client.connect(broker_address, broker_port)
    return client


def run():
    """Run the MQTT monitor"""

    client = mqtt_connect()
    for topic in topics:
        client.subscribe(topic)

    client.loop_start()

    try:
        while True:
            time.sleep(0.5)

    except:
        client.disconnect()
        client.loop_stop()

    run()


if __name__ == "__main__":
    run()
