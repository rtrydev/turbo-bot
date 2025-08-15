from dataclasses import dataclass

from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.services.context_manager_service import ContextManagerService
from backend.domain.services.media_player_service import MediaPlayerService


@dataclass
class StartQueuePlaybackCommand(Request[None]):
    pass

class StartQueuePlaybackCommandHandler(RequestHandler[StartQueuePlaybackCommand, None]):
    __context_manager_service: ContextManagerService
    __media_player_service: MediaPlayerService

    def __init__(self, context_manager_service: ContextManagerService, media_player_service: MediaPlayerService) -> None:
        self.__context_manager_service = context_manager_service
        self.__media_player_service = media_player_service

    def handle(self, request: StartQueuePlaybackCommand) -> None:
        queue_state = self.__context_manager_service.get_queue_state()
        next_song = queue_state.get_next()

        if next_song is None:
            raise ValueError("No songs in the queue to play.")

        self.__media_player_service.play(next_song)
