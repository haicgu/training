#!/usr/bin/env python

import os
import platform
import random
from paho.mqtt import client as mqtt_client


# broker = 'localhost'           # Broker in container should be used for the tutorial
# broker = 'broker.emqx.io'       # Free public MQTT broker
# port = 1883
# topic = 'test'
broker = os.getenv("BROKER_ADDRESS", "broker.emqx.io")  # Free public MQTT broker
port = int(os.getenv("BROKER_PORT", "1883"))
topic = os.getenv("TOPIC", "test")
node = platform.node()

# Generate a Client ID with the subscribe prefix.
client_id = f"subscriber-{random.randint(0, 100)}"


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from topc `{msg.topic}`")

    client.subscribe(topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == "__main__":
    run()
