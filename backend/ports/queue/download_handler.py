from backend.application.commands.download_song_command import DownloadSongCommand
from backend.domain.services.download_queue_service import DownloadQueueService
from backend.service.application_service import get_mediator
from backend.service.dependency_injection import container

if __name__ == '__main__':
    mediator = get_mediator()

    def processor(song_dict: dict) -> None:
        mediator.send(DownloadSongCommand(
            id=song_dict['id'],
            origin=song_dict['origin']
        ))

    download_queue: DownloadQueueService = container.resolve(DownloadQueueService)
    download_queue.register_message_observer(processor)
