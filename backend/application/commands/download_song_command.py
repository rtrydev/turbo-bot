from dataclasses import dataclass

from backend.application.dtos.song_download_dto import SongDownloadDTO
from backend.application.errors.song_already_downloaded_error import SongAlreadyDownloadedError
from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.repositories.song_repository import SongRepository
from backend.domain.services.media_download_service import MediaDownloadService


@dataclass
class DownloadSongCommand(Request[None], SongDownloadDTO):
    id: str
    origin: str

    @staticmethod
    def from_dto(schema: SongDownloadDTO) -> 'DownloadSongCommand':
        return DownloadSongCommand(
            id=schema.id,
            origin=schema.origin
        )

class DownloadSongCommandHandler(RequestHandler[DownloadSongCommand, None]):
    __song_repository: SongRepository
    __media_download_service: MediaDownloadService

    def __init__(self, song_repository: SongRepository, media_download_service: MediaDownloadService):
        self.__song_repository = song_repository
        self.__media_download_service = media_download_service

    def handle(self, request: DownloadSongCommand) -> None:
        song = self.__song_repository.get_by_id(request.id)

        if song is None:
            raise Exception(f'Song with id {request.id} not found')

        if song.fid is not None:
            raise SongAlreadyDownloadedError(request.id)

        song.fid = self.__media_download_service.download_song(song)
        self.__song_repository.update(song)
