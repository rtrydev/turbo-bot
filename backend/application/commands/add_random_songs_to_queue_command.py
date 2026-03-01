from attr import dataclass

from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.repositories.song_repository import SongRepository
from backend.domain.services.context_manager_service import ContextManagerService


@dataclass
class AddRandomSongsToQueueCommand(Request[None]):
    count: int

class AddRandomSongsToQueueCommandHandler(RequestHandler[AddRandomSongsToQueueCommand, None]):
    __song_repository: SongRepository
    __context_manager_service: ContextManagerService

    def __init__(self, song_repository: SongRepository, context_manager_service: ContextManagerService) -> None:
        self.__song_repository = song_repository
        self.__context_manager_service = context_manager_service

    def handle(self, request: AddRandomSongsToQueueCommand) -> None:
        songs = self.__song_repository.get_random(request.count)

        if not songs:
            raise ValueError('No songs found in the database.')

        queue = self.__context_manager_service.get_queue_state()
        for song in songs:
            queue.add(song)
