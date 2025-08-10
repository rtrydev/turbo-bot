from punq import Scope

from backend.adapters.providers.youtube_song_metadata_provider import YoutubeSongMetadataProvider
from backend.adapters.repositories.in_memory.in_memory_song_repository import InMemorySongRepository
from backend.application.commands.create_song_command import CreateSongCommand, CreateSongCommandHandler
from backend.application.queries.get_song_by_id_query import GetSongByIdQuery, GetSongByIdQueryHandler
from backend.application.utils.mediator import Mediator
from backend.domain.repositories.song_repository import SongRepository
from backend.service.dependency_injection import container

def get_mediator() -> Mediator:
    container.register(SongRepository, InMemorySongRepository, scope=Scope.singleton)

    container.register(YoutubeSongMetadataProvider)

    return Mediator()\
        .register(CreateSongCommand, CreateSongCommandHandler)\
        .register(GetSongByIdQuery, GetSongByIdQueryHandler)
