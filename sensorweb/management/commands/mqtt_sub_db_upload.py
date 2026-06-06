# management/commands/mqtt_subscribe.py
import json
from django.core.management.base import BaseCommand
from sensorweb.models import sensors
import paho.mqtt.client as mqtt
import time

BROKER = "192.168.0.44"
PORT = 1883
TOPIC = "iot/sensors/data"

class Command(BaseCommand):
    help = "Subscribe to MQTT and save data to the database"

    def __init__(self):    
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
            client.subscribe(TOPIC, 1)
        else:
            print(f"Failed to connect, return code {rc}")
            # 연결 실패 시 10초 후 재시도
            time.sleep(10)
            client.reconnect()

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            payload = json.loads(payload)
            print(f'payload = {payload} type = {type(payload)}')

            # sensors(
            #     type = payload['type'],
            #     time = payload['time'],
            #     location = payload['location'],
            #     temp_left = payload['temp_left'],
            #     temp_right = payload['temp_right'],
            #     load_left = payload['load_left'],
            #     load_right = payload['load_right'],
            #     vocs = payload['vocs'],
            #     vocs_temp = payload['vocs_temp'],
            #     vocs_hum = payload['vocs_hum'],
            # ).save()
        except Exception as e:
            print(f"Error: {e}")


    def handle(self, *args, **kwargs):
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.connect(BROKER, PORT)
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("Stopped subscription.")
        finally:
            self.client.disconnect()  # MQTT 클라이언트 연결 해제
