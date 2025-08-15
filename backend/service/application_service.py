import os

from punq import Scope
from pymongo import MongoClient

from backend.adapters.providers.youtube_song_metadata_provider import YoutubeSongMetadataProvider
from backend.adapters.repositories.mongo.mongodb_song_repository import MongoDBSongRepository
from backend.adapters.services.rabbitmq_download_queue_service import RabbitMQDownloadQueueService
from backend.adapters.services.seaweedfs_filesystem_service import SeaweedfsFilesystemService
from backend.adapters.services.youtube_media_download_service import YoutubeMediaDownloadService
from backend.application.commands.create_song_command import CreateSongCommand, CreateSongCommandHandler
from backend.application.commands.download_song_command import DownloadSongCommand, DownloadSongCommandHandler
from backend.application.providers.saved_audio_provider import SavedAudioProvider
from backend.application.providers.stream_audio_provider import StreamAudioProvider
from backend.application.queries.get_song_by_id_query import GetSongByIdQuery, GetSongByIdQueryHandler
from backend.application.utils.mediator import Mediator
from backend.domain.repositories.song_repository import SongRepository
from backend.domain.services.download_queue_service import DownloadQueueService
from backend.domain.services.filesystem_service import FilesystemService
from backend.domain.services.media_download_service import MediaDownloadService
from backend.service.dependency_injection import container

def get_mediator() -> Mediator:
    seaweedfs_url = os.environ.get('SEAWEEDFS_URL', 'http://localhost:9333')
    rabbitmq_user = os.environ.get('RABBITMQ_DEFAULT_USER', 'guest')
    rabbitmq_password = os.environ.get('RABBITMQ_DEFAULT_PASS', 'guest')
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')

    container.register(MongoClient, lambda: MongoClient(mongo_uri), scope=Scope.singleton)

    container.register(SongRepository, MongoDBSongRepository, scope=Scope.singleton)

    container.register(DownloadQueueService, lambda: RabbitMQDownloadQueueService(rabbitmq_user, rabbitmq_password), scope=Scope.singleton)
    container.register(FilesystemService, lambda: SeaweedfsFilesystemService(*seaweedfs_url.split(':')), scope=Scope.singleton)
    container.register(MediaDownloadService, YoutubeMediaDownloadService)

    container.register(SavedAudioProvider)
    container.register(StreamAudioProvider)
    container.register(YoutubeSongMetadataProvider)

    return Mediator()\
        .register(CreateSongCommand, CreateSongCommandHandler)\
        .register(GetSongByIdQuery, GetSongByIdQueryHandler)\
        .register(DownloadSongCommand, DownloadSongCommandHandler)
