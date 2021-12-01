import pika
import os
import traceback
import threading
import json
import sys
from types import FunctionType


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_crowdsale.settings')
import django
django.setup()

from django.core.exceptions import ObjectDoesNotExist
from gold_crowdsale.settings import NETWORKS
from gold_crowdsale.payments.api import parse_payment_message
from gold_crowdsale.transfers.models import parse_transfer_confirmation


class Receiver(threading.Thread):

    def __init__(self, queue):
        super().__init__()
        self.network = queue

    def run(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            'rabbitmq',
            5672,
            os.getenv('RABBITMQ_DEFAULT_VHOST', 'gold_crowdsale'),
            pika.PlainCredentials(os.getenv('RABBITMQ_DEFAULT_USER', 'gold_crowdsale'),
                                  os.getenv('RABBITMQ_DEFAULT_PASS', 'gold_crowdsale')),
            heartbeat=3600,
            blocked_connection_timeout=3600
        ))

        channel = connection.channel()

        queue_name = NETWORKS.get(self.network).get('queue')

        channel.queue_declare(
                queue=queue_name,
                durable=True,
                auto_delete=False,
                exclusive=False
        )
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=self.callback
        )

        print(
            'RECEIVER: started on {net} with queue `{queue_name}`'
            .format(net=self.network, queue_name=queue_name), flush=True
        )

        channel.start_consuming()

    def payment(self, message):
        print('RECEIVER: payment message received', flush=True)
        parse_payment_message(message)

    def transferred(self, message):
        print('TRANSFER CONFIRMATION RECEIVED', flush=True)
        parse_transfer_confirmation(message)

    def callback(self, ch, method, properties, body):
        print('RECEIVER: received', body, properties, method, flush=True)
        try:
            message = json.loads(body.decode())
            if message.get('status', '') == 'COMMITTED':
                getattr(self, properties.type, self.unknown_handler)(message)
        except Exception as e:
            print('\n'.join(traceback.format_exception(*sys.exc_info())),
                  flush=True)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def unknown_handler(self, message):
        print('RECEIVER: unknown message', message, flush=True)


networks = NETWORKS.keys()


for network in networks:
    rec = Receiver(network)
    rec.start()
