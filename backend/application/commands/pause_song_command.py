from dataclasses import dataclass

from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.services.media_player_service import MediaPlayerService


@dataclass
class PauseSongCommand(Request[None]):
    pass

class PauseSongCommandHandler(RequestHandler[PauseSongCommand, None]):
    __media_player_service: MediaPlayerService

    def __init__(self, media_player_service: MediaPlayerService) -> None:
        self.__media_player_service = media_player_service

    def handle(self, request: PauseSongCommand) -> None:
        self.__media_player_service.pause()
