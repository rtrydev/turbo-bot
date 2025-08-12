from dataclasses import dataclass

from backend.application.dtos.song_create_dto import SongCreateDTO
from backend.application.dtos.song_create_response_dto import SongCreateResponseDTO
from backend.application.factories.song_metadata_provider_factory import SongMetadataProviderFactory
from backend.application.factories.url_parser_factory import UrlParserFactory
from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.models.song import Song
from backend.domain.repositories.song_repository import SongRepository
from backend.domain.services.media_download_service import MediaDownloadService


@dataclass
class CreateSongCommand(Request[SongCreateResponseDTO], SongCreateDTO):
    @staticmethod
    def from_dto(schema: SongCreateDTO) -> 'CreateSongCommand':
        return CreateSongCommand(
            origin=schema.origin
        )

class CreateSongCommandHandler(RequestHandler[CreateSongCommand, SongCreateResponseDTO]):
    __song_repository: SongRepository
    __media_download_service: MediaDownloadService

    def __init__(self, song_repository: SongRepository, media_download_service: MediaDownloadService):
        self.__song_repository = song_repository
        self.__media_download_service = media_download_service

    def handle(self, request: CreateSongCommand) -> SongCreateResponseDTO:
        song_id = UrlParserFactory.create(request.origin).get_id()
        song_meta = SongMetadataProviderFactory.create(request.origin).get_meta(song_id)

        song = Song(
            id=song_id,
            fid=None,
            origin=request.origin,
            length=song_meta.length,
            title=song_meta.title
        )

        self.__song_repository.create(song)
        song.fid = self.__media_download_service.download_song(song) # todo: do this asynchronously

        return SongCreateResponseDTO(
            id=song.id,
            origin=song.origin,
            title=song.title,
            length=song.length
        )