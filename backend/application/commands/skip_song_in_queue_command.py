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
        # Remember what the user just skipped so repeat mode (which normally
        # re-plays the last track on song end) does not bring it back — a
        # skip means "do not come back to this one".
        queue_state.skip_excluding(queue_state.get_last_song())

        # Advancing to the next track (which also records it as the current
        # one) is the *only* state change: the previously playing song simply
        # leaves the "current" slot.
        self.__media_player_service.next()
