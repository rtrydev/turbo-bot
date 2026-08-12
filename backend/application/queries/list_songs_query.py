from dataclasses import dataclass

from backend.application.dtos.admin_dto import SongsListResponseDTO
from backend.application.dtos.song_dto import SongDTO
from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.repositories.song_repository import SongRepository


@dataclass
class ListSongsQuery(Request[SongsListResponseDTO]):
    query: str = ''
    page: int = 0
    limit: int = 25


class ListSongsQueryHandler(RequestHandler[ListSongsQuery, SongsListResponseDTO]):
    __song_repository: SongRepository

    def __init__(self, song_repository: SongRepository) -> None:
        self.__song_repository = song_repository

    def handle(self, request: ListSongsQuery) -> SongsListResponseDTO:
        songs, total = self.__song_repository.find(
            query=request.query,
            page=request.page,
            limit=request.limit
        )

        return SongsListResponseDTO(
            songs=[SongDTO(id=s.id, title=s.title, length=s.length, origin=s.origin) for s in songs],
            total=total,
            page=request.page,
            limit=request.limit
        )
