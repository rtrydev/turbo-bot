import asyncio
from dataclasses import dataclass

from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.providers.channel_connection_provider import ChannelConnectionProvider
from backend.domain.services.context_manager_service import ContextManagerService
from backend.domain.services.media_player_service import MediaPlayerService


@dataclass
class LeaveChannelCommand(Request[None]):
    pass

class LeaveChannelCommandHandler(RequestHandler[LeaveChannelCommand, None]):
    __channel_connection_provider: ChannelConnectionProvider
    __context_manager_service: ContextManagerService
    __media_player_service: MediaPlayerService

    def __init__(self, channel_connection_provider: ChannelConnectionProvider, context_manager_service: ContextManagerService, media_player_service: MediaPlayerService) -> None:
        self.__channel_connection_provider = channel_connection_provider
        self.__context_manager_service = context_manager_service
        self.__media_player_service = media_player_service

    def handle(self, request: LeaveChannelCommand) -> None:
        # Reset the whole playback state: drop the queued tracks and the
        # current song, and stop the audio. Leaving a channel ends the
        # session entirely.
        channel = self.__channel_connection_provider.get_channel_connection()
        if channel is not None and (channel.is_playing() or channel.is_paused()):
            self.__media_player_service.stop()

        # The slot resets (and any resulting queue-change events) come
        # *after* the audio is stopped: an observer that snapshots state
        # while audio is still alive must never report an empty "now
        # playing" for a track that is still going.
        queue_state = self.__context_manager_service.get_queue_state()
        queue_state.clear()
        queue_state.reset_current()

        asyncio.create_task(
            self.__channel_connection_provider.disconnect_from_channel()
        )
