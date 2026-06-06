# myapp/management/commands/fetch_data.py
from django.core.management.base import BaseCommand
from sensorweb.models import sensors
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time

class Command(BaseCommand):
    help = 'Fetch data from MariaDB and send to WebSocket'

    def handle(self, *args, **kwargs):
        while True:
            sensors_data = sensors.objects.all().order_by('-time')[:20]
            data = list(sensors_data.values())
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "sensor_group",
                {
                    "type": "sensor_data",
                    "data": data,
                }
            )
            time.sleep(1)
