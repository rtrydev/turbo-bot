import json
from dataclasses import dataclass, asdict

from backend.application.dtos.song_create_dto import SongCreateDTO
from backend.application.dtos.song_create_response_dto import SongCreateResponseDTO
from backend.application.factories.song_metadata_provider_factory import SongMetadataProviderFactory
from backend.application.factories.url_parser_factory import UrlParserFactory
from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.models.song import Song
from backend.domain.repositories.song_repository import SongRepository
from backend.domain.services.download_queue_service import DownloadQueueService


@dataclass
class CreateSongCommand(Request[SongCreateResponseDTO], SongCreateDTO):
    origin: str

    @staticmethod
    def from_dto(schema: SongCreateDTO) -> 'CreateSongCommand':
        return CreateSongCommand(
            origin=schema.origin
        )

class CreateSongCommandHandler(RequestHandler[CreateSongCommand, SongCreateResponseDTO]):
    __song_repository: SongRepository
    __download_queue_service: DownloadQueueService

    def __init__(self, song_repository: SongRepository, download_queue_service: DownloadQueueService):
        self.__song_repository = song_repository
        self.__download_queue_service = download_queue_service

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
        self.__download_queue_service.send_message(
            json.dumps(asdict(song))
        )

        return SongCreateResponseDTO(
            id=song.id,
            origin=song.origin,
            title=song.title,
            length=song.length
        )