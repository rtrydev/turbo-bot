from dataclasses import dataclass
from typing import Optional

from backend.application.dtos.song_get_dto import SongGetDTO
from backend.application.dtos.song_get_response_dto import SongGetResponseDTO
from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.repositories.song_repository import SongRepository


@dataclass
class GetSongByIdQuery(Request[Optional[SongGetResponseDTO]], SongGetDTO):
    id: str

    @staticmethod
    def from_dto(schema: SongGetDTO) -> 'GetSongByIdQuery':
        return GetSongByIdQuery(
            id=schema.id
        )

class GetSongByIdQueryHandler(RequestHandler[GetSongByIdQuery, SongGetResponseDTO]):
    __song_repository: SongRepository

    def __init__(self, song_repository: SongRepository):
        self.__song_repository = song_repository

    def handle(self, request: GetSongByIdQuery) -> Optional[SongGetResponseDTO]:
        song = self.__song_repository.get_by_id(request.id)

        if song is None:
            return None

        return SongGetResponseDTO(
            id= song.id,
            origin=song.origin,
            title=song.title,
            length=song.length
        )
