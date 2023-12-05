#!/usr/bin/env python

import os
import random
import time
import platform
from paho.mqtt import client as mqtt_client


# broker = 'localhost'           # Broker in container should be used for the tutorial
# broker = 'broker.emqx.io'       # Free public MQTT broker
# port = 1883
# topic = 'test'

broker = os.getenv("BROKER_ADDRESS", "broker.emqx.io")  # Free public MQTT broker
port = int(os.getenv("BROKER_PORT", "1883"))
topic = os.getenv("TOPIC", "test")
node = platform.node()

# Generate a Client ID with the publish prefix.
client_id = f"publisher-{random.randint(0, 1000)}"


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

# Let it run a bit longer to avoid CrashLoopBacks..
def publish(client):
    msg_count = 1
    while msg_count < 10000:
        time.sleep(3)
        msg = f"node={node}, message counter={msg_count}"
        result = client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        msg_count += 1

def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    client.loop_stop()


if __name__ == "__main__":
    run()
