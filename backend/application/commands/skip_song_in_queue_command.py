from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.services.context_manager_service import ContextManagerService
from backend.domain.services.media_player_service import MediaPlayerService


class SkipSongInQueueCommand(Request[None]):
    pass

class SkipSongInQueueCommandHandler(RequestHandler[SkipSongInQueueCommand, None]):
    __context_manager_service: ContextManagerService
    __media_player_service: MediaPlayerService

    def __init__(self, context_manager_service: ContextManagerService, media_player_service: MediaPlayerService) -> None:
        self.__context_manager_service = context_manager_service
        self.__media_player_service = media_player_service

    def handle(self, request: SkipSongInQueueCommand) -> None:
        queue_state = self.__context_manager_service.get_queue_state()
        queue_state.skip()

        self.__media_player_service.next()
