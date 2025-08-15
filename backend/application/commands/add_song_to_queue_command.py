from attr import dataclass

from backend.application.factories.url_parser_factory import UrlParserFactory
from backend.application.utils.mediator import Request, RequestHandler

from backend.application.dtos.song_add_to_queue_dto import SongAddToQueueDTO
from backend.domain.repositories.song_repository import SongRepository
from backend.domain.services.context_manager_service import ContextManagerService


@dataclass
class AddSongToQueueCommand(Request[None], SongAddToQueueDTO):
    origin: str

    @staticmethod
    def from_dto(schema: SongAddToQueueDTO) -> 'AddSongToQueueCommand':
        return AddSongToQueueCommand(
            origin=schema.origin
        )

class AddSongToQueueCommandHandler(RequestHandler[AddSongToQueueCommand, None]):
    __song_repository: SongRepository
    __context_manager_service: ContextManagerService

    def __init__(self, song_repository: SongRepository, context_manager_service: ContextManagerService) -> None:
        self.__song_repository = song_repository
        self.__context_manager_service = context_manager_service

    def handle(self, request: AddSongToQueueCommand) -> None:
        song_id = UrlParserFactory.create(request.origin).get_id()

        song = self.__song_repository.get_by_id(song_id)

        if song is None:
            raise ValueError(f'Song with ID {song_id} not found in repository.')

        self.__context_manager_service.get_queue_state().add(song)
