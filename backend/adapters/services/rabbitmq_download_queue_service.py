import time
from typing import Callable

import pika
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

        channel = connection.channel()
        channel.queue_declare(queue=self.__queue_name)

        channel.basic_consume(
            queue=self.__queue_name,
            on_message_callback=callback,
            auto_ack=True
        )
        channel.start_consuming()

    def send_message(self, message: str) -> None:
        connection = self.__get_connection()

        channel = connection.channel()
        channel.queue_declare(queue=self.__queue_name)

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
