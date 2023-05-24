import datetime
import logging
import os
from dotenv import load_dotenv

import pymysql
from sqlalchemy import create_engine
import pandas as pd
import paho.mqtt.client as mqtt

LOGGER = logging.getLogger()

load_dotenv()

broker_address = os.environ["BROKER_ADDRESS"]
broker_port = int(os.environ["BROKER_PORT"])
topics = ["TEMPERATURE_INSIDE", "HUMIDITY_INSIDE"]

sql_engine = create_engine(f"mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}/{os.environ['DB']}", pool_recycle=3600)
db_connection = sql_engine.connect()


def on_message(client, userdata, message):
    """Handle a message from the MQTT broker"""
    df = pd.DataFrame([[datetime.datetime.utcnow().isoformat(), message.payload.decode()]], columns=["date", message.topic])
    df.to_sql(message.topic, db_connection, if_exists="append", index=False)
    LOGGER.info(f"Message received and saved to file {message.topic}:  {message.payload.decode()}")


def run():
    """Run the MQTT monitor"""
    client = mqtt.Client()
    client.on_message = on_message
    client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
    client.username_pw_set(os.environ["MQTT_USERNAME"], os.environ["MQTT_PASSWORD"])
    client.connect(broker_address, broker_port)

    for topic in topics:
        client.subscribe(topic)

    client.loop_start()

    try:
        while True:
            pass

    except KeyboardInterrupt:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    run()