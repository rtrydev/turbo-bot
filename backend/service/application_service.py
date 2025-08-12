import os

from punq import Scope

from backend.adapters.providers.youtube_song_metadata_provider import YoutubeSongMetadataProvider
from backend.adapters.repositories.in_memory.in_memory_song_repository import InMemorySongRepository
from backend.adapters.services.seaweedfs_filesystem_service import SeaweedfsFilesystemService
from backend.adapters.services.youtube_media_download_service import YoutubeMediaDownloadService
from backend.application.commands.create_song_command import CreateSongCommand, CreateSongCommandHandler
from backend.application.queries.get_song_by_id_query import GetSongByIdQuery, GetSongByIdQueryHandler
from backend.application.utils.mediator import Mediator
from backend.domain.repositories.song_repository import SongRepository
from backend.domain.services.filesystem_service import FilesystemService
from backend.domain.services.media_download_service import MediaDownloadService
from backend.service.dependency_injection import container

def get_mediator() -> Mediator:
    seaweedfs_url = os.environ.get('SEAWEEDFS_URL', 'http://localhost:9333')

    container.register(SongRepository, InMemorySongRepository, scope=Scope.singleton)

    container.register(FilesystemService, lambda: SeaweedfsFilesystemService(*seaweedfs_url.split(':')), scope=Scope.singleton)
    container.register(MediaDownloadService, YoutubeMediaDownloadService)

    container.register(YoutubeSongMetadataProvider)

    return Mediator()\
        .register(CreateSongCommand, CreateSongCommandHandler)\
        .register(GetSongByIdQuery, GetSongByIdQueryHandler)
