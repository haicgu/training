#!/usr/bin/env python

import platform
import time
import random
import os
from paho.mqtt import client as mqtt_client


#broker = 'localhost'           # Broker in container should be used for the tutorial
broker = 'broker.emqx.io'       # Free public MQTT broker
broker = os.getenv("BROKER_ADDRESS", "broker.emqx.io")  # Free public MQTT broker
port = int(os.getenv("BROKER_PORT", "1883"))
topic_collector = os.getenv("TOPIC_COLLECTOR", "data-collector")
topic_aggregator = os.getenv("TOPIC_AGGREGATOR", "data-aggregator")
time_publish = 5
node = platform.node()

# Generate a Client ID with the publish prefix.
client_id = f'cloud-{random.randint(0, 1000)}'


class Timer:
    def __init__(self, delta):
        self.tstart = None
        self.tstop = None
        self.delta = delta

    def start(self):
        self.tstart = time.time()
        self.tstop = self.tstart + self.delta

    def check(self):
        return (time.time() > self.tstop)


timer = Timer(time_publish)


class Collector:
    def __init__(self):
        self.sum = 0
        self.cnt = 0

    def add(self, x):
        self.sum += x
        self.cnt += 1

    def avg(self):
        return self.sum / self.cnt


load = Collector()


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


def aggregate_publish(client):
    def on_message(client, userdata, msg):
        global load

        payload = msg.payload.decode()
        sender, val = payload.split(";")
        print(f"Received `{payload}` from topic `{msg.topic}`")

        load.add(float(val))

        if (timer.check()):
            avg = load.avg()
            msg = f"{node};{avg}"
            result = client.publish(topic_aggregator, msg)
            # result: [0, 1]
            status = result[0]
            if status == 0:
                print(f"Send `{msg}` to topic `{topic_aggregator}`")
            else:
                print(f"Failed to send message to topic {topic_aggregator}")

            timer.start()

    client.subscribe(topic_collector)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    #client.loop_start()
    timer.start()
    aggregate_publish(client)
    client.loop_forever()


if __name__ == '__main__':
    run()
