import json

from backend.application.commands.download_song_command import DownloadSongCommand
from backend.domain.services.download_queue_service import DownloadQueueService
from backend.service.application_service import get_mediator
from backend.service.dependency_injection import container

if __name__ == '__main__':
    mediator = get_mediator()

    def handler(channel, method, properties, body) -> None:
        headers = properties.headers or {}
        death_info = headers.get('x-death', [])

        retry_count = 0
        if death_info:
            retry_count = death_info[0].get('count', 0)

        print(f'Received message: {body}, Retry count: {retry_count}')
        song_dict = json.loads(body)

        try:
            mediator.send(DownloadSongCommand(
                id=song_dict['id'],
                origin=song_dict['origin']
            ))
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f'Error processing message: {e}')

            if retry_count < 3:
                print(f'Failing message, will retry (count={retry_count + 1})')
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            else:
                print('Max retries reached, moving to dead-letter queue')
                channel.basic_ack(delivery_tag=method.delivery_tag)

    download_queue: DownloadQueueService = container.resolve(DownloadQueueService)
    download_queue.register_message_observer(handler)
