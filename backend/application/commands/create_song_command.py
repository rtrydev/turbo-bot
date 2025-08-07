from uuid import uuid4
from dataclasses import dataclass, asdict

from backend.application.dtos.song_create_dto import SongCreateDTO
from backend.application.dtos.song_create_response_dto import SongCreateResponseDTO
from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.models.song import Song
from backend.domain.repositories.song_repository import SongRepository


@dataclass
class CreateSongCommand(Request[SongCreateResponseDTO], SongCreateDTO):
    @staticmethod
    def from_dto(schema: SongCreateDTO) -> 'CreateSongCommand':
        return CreateSongCommand(
            origin=schema.origin
        )

class CreateSongCommandHandler(RequestHandler[CreateSongCommand, SongCreateResponseDTO]):
    __song_repository: SongRepository

    def __init__(self, song_repository: SongRepository):
        self.__song_repository = song_repository

    def handle(self, request: CreateSongCommand) -> SongCreateResponseDTO:
        song = Song(
            id=str(uuid4()),
            origin=request.origin,
            length=420,
            title='Never gonna give you up'
        )

        self.__song_repository.create(song)

        return SongCreateResponseDTO(
            **asdict(song)
        )