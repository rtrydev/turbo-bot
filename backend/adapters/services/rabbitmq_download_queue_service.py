import time
from typing import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from pika.exceptions import AMQPConnectionError

from backend.domain.services.download_queue_service import DownloadQueueService


class RabbitMQDownloadQueueService(DownloadQueueService):
    __queue_name = 'download_queue'
    __queue_user: str
    __queue_password: str

    def __init__(self, queue_user: str, queue_password: str):
        self.__queue_user = queue_user
        self.__queue_password = queue_password

    def register_message_observer(self, callback: Callable) -> None:
        connection = self.__get_connection()

        channel = self.__get_channel(connection)
        channel.basic_consume(
            queue=self.__queue_name,
            on_message_callback=callback,
            auto_ack=False
        )
        channel.start_consuming()

    def send_message(self, message: str) -> None:
        connection = self.__get_connection()

        channel = self.__get_channel(connection)
        channel.basic_publish(
            exchange='',
            routing_key=self.__queue_name,
            body=message.encode('utf-8')
        )
        connection.close()

    def __get_connection(self) -> pika.BlockingConnection:
        connection = None

        for attempt in range(10):
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        'rabbitmq',
                        credentials=pika.PlainCredentials(
                            username=self.__queue_user,
                            password=self.__queue_password
                        )
                    )
                )
                break
            except AMQPConnectionError:
                if attempt == 9:
                    raise Exception('Failed to connect to RabbitMQ after 10 attempts')
                else:
                    print(f'Connection attempt {attempt + 1} failed, retrying...')
                    time.sleep(3)

        return connection

    def __get_channel(self, connection: BlockingConnection) -> BlockingChannel:
        channel = connection.channel()

        channel.queue_declare(queue=f'{self.__queue_name}_dlq', durable=True)

        channel.queue_declare(
            queue=f'{self.__queue_name}_retry',
            durable=True,
            arguments={
                'x-dead-letter-exchange': '',
                'x-dead-letter-routing-key': self.__queue_name,
                'x-message-ttl': 5000
            }
        )

        channel.queue_declare(
            queue=self.__queue_name,
            durable=True,
            arguments={
                'x-dead-letter-exchange': '',
                'x-dead-letter-routing-key': f'{self.__queue_name}_retry'
            }
        )

        return channel
