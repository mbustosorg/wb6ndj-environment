import datetime
import os
import logging
import sys
from dotenv import load_dotenv

import paho.mqtt.client as mqtt

DEFAULT_LEVEL = logging.INFO
FORMATTER = logging.Formatter(
    "%(asctime)s|%(process)d|%(module)s|%(levelname)s|%(message)s"
)
LOGGER = logging.getLogger()
LOGGER.setLevel(DEFAULT_LEVEL)
LOGGER.handlers = []
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(DEFAULT_LEVEL)
handler.setFormatter(FORMATTER)
LOGGER.addHandler(handler)

load_dotenv()

broker_address = os.environ["BROKER_ADDRESS"]
broker_port = int(os.environ["BROKER_PORT"])
topics = ["TEMPERATURE_INSIDE", "HUMIDITY_INSIDE"]


def on_message(client, userdata, message):
    """Handle a message from the MQTT broker"""
    with open(f"{message.topic}.txt", 'a') as file:
        file.write(f"{datetime.datetime.utcnow().isoformat()},{message.payload.decode()}\n")
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