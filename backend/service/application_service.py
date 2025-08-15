import os

import discord
from punq import Scope
from pymongo import MongoClient

from backend.adapters.providers.discord_channel_connection_provider import DiscordChannelConnectionProvider
from backend.adapters.providers.youtube_song_metadata_provider import YoutubeSongMetadataProvider
from backend.adapters.repositories.mongo.mongodb_song_repository import MongoDBSongRepository
from backend.adapters.services.discord_media_player_service import DiscordMediaPlayerService
from backend.adapters.services.in_memory_context_manager_service import InMemoryContextManagerService
from backend.adapters.services.rabbitmq_download_queue_service import RabbitMQDownloadQueueService
from backend.adapters.services.seaweedfs_filesystem_service import SeaweedfsFilesystemService
from backend.adapters.services.youtube_media_download_service import YoutubeMediaDownloadService
from backend.application.commands.add_song_to_queue_command import AddSongToQueueCommand, AddSongToQueueCommandHandler
from backend.application.commands.create_song_command import CreateSongCommand, CreateSongCommandHandler
from backend.application.commands.download_song_command import DownloadSongCommand, DownloadSongCommandHandler
from backend.application.commands.join_channel_command import JoinChannelCommand, JoinChannelCommandHandler
from backend.application.commands.leave_channel_command import LeaveChannelCommand, LeaveChannelCommandHandler
from backend.application.commands.pause_song_command import PauseSongCommand, PauseSongCommandHandler
from backend.application.commands.resume_song_command import ResumeSongCommand, ResumeSongCommandHandler
from backend.application.commands.skip_song_in_queue_command import SkipSongInQueueCommand, \
    SkipSongInQueueCommandHandler
from backend.application.commands.start_queue_playback_command import StartQueuePlaybackCommand, \
    StartQueuePlaybackCommandHandler
from backend.application.commands.toggle_repeat_command import ToggleRepeatCommand, ToggleRepeatCommandHandler
from backend.application.providers.saved_audio_provider import SavedAudioProvider
from backend.application.providers.stream_audio_provider import StreamAudioProvider
from backend.application.queries.get_song_by_id_query import GetSongByIdQuery, GetSongByIdQueryHandler
from backend.application.utils.mediator import Mediator
from backend.domain.providers.channel_connection_provider import ChannelConnectionProvider
from backend.domain.repositories.song_repository import SongRepository
from backend.domain.services.context_manager_service import ContextManagerService
from backend.domain.services.download_queue_service import DownloadQueueService
from backend.domain.services.filesystem_service import FilesystemService
from backend.domain.services.media_download_service import MediaDownloadService
from backend.domain.services.media_player_service import MediaPlayerService
from backend.service.dependency_injection import container

def get_mediator(discord_connect=False) -> Mediator:
    seaweedfs_url = os.environ.get('SEAWEEDFS_URL', 'http://localhost:9333')
    rabbitmq_user = os.environ.get('RABBITMQ_DEFAULT_USER', 'guest')
    rabbitmq_password = os.environ.get('RABBITMQ_DEFAULT_PASS', 'guest')
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')

    if discord_connect:
        discord_client_id = os.environ.get('DISCORD_CLIENT_ID')
        discord_guild_id = os.environ.get('DISCORD_GUILD_ID')

        discord_client = discord.Client(
            intents=discord.Intents(discord.Intents.guilds.flag | discord.Intents.guild_messages.flag | discord.Intents.voice_states.flag),
            client_id=discord_client_id,
            guild_id=int(discord_guild_id) if discord_guild_id else None
        )

        container.register(discord.Client, lambda: discord_client, scope=Scope.singleton)
        container.register(ChannelConnectionProvider, DiscordChannelConnectionProvider, scope=Scope.singleton)
        container.register(MediaPlayerService, DiscordMediaPlayerService)

    container.register(MongoClient, lambda: MongoClient(mongo_uri), scope=Scope.singleton)

    container.register(SongRepository, MongoDBSongRepository, scope=Scope.singleton)

    container.register(DownloadQueueService, lambda: RabbitMQDownloadQueueService(rabbitmq_user, rabbitmq_password), scope=Scope.singleton)
    container.register(FilesystemService, lambda: SeaweedfsFilesystemService(*seaweedfs_url.split(':')), scope=Scope.singleton)
    container.register(MediaDownloadService, YoutubeMediaDownloadService)
    container.register(ContextManagerService, InMemoryContextManagerService, scope=Scope.singleton)

    container.register(SavedAudioProvider)
    container.register(StreamAudioProvider)
    container.register(YoutubeSongMetadataProvider)

    return Mediator()\
        .register(CreateSongCommand, CreateSongCommandHandler)\
        .register(GetSongByIdQuery, GetSongByIdQueryHandler)\
        .register(DownloadSongCommand, DownloadSongCommandHandler)\
        .register(AddSongToQueueCommand, AddSongToQueueCommandHandler)\
        .register(JoinChannelCommand, JoinChannelCommandHandler)\
        .register(LeaveChannelCommand, LeaveChannelCommandHandler)\
        .register(PauseSongCommand, PauseSongCommandHandler)\
        .register(ResumeSongCommand, ResumeSongCommandHandler)\
        .register(SkipSongInQueueCommand, SkipSongInQueueCommandHandler)\
        .register(StartQueuePlaybackCommand, StartQueuePlaybackCommandHandler)\
        .register(ToggleRepeatCommand, ToggleRepeatCommandHandler)
