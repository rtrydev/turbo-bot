from dataclasses import dataclass

from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.repositories.song_repository import SongRepository
from backend.domain.services.context_manager_service import ContextManagerService
from backend.domain.services.filesystem_service import FilesystemService


@dataclass
class DeleteSongCommand(Request[None]):
    id: str


class DeleteSongCommandHandler(RequestHandler[DeleteSongCommand, None]):
    __song_repository: SongRepository
    __context_manager_service: ContextManagerService
    __filesystem_service: FilesystemService

    def __init__(
        self,
        song_repository: SongRepository,
        context_manager_service: ContextManagerService,
        filesystem_service: FilesystemService
    ) -> None:
        self.__song_repository = song_repository
        self.__context_manager_service = context_manager_service
        self.__filesystem_service = filesystem_service

    def handle(self, request: DeleteSongCommand) -> None:
        song = self.__song_repository.get_by_id(request.id)

        if song is None:
            raise ValueError(f'Song with ID {request.id} not found in repository.')

        # Remove only queued (not yet played) occurrences. If the deleted
        # track is the current one it keeps playing — the queue view is a
        # snapshot of live state and must not "unplay" a song mid-track.
        queue_state = self.__context_manager_service.get_queue_state()
        current = queue_state.get_last_song()
        if current is not None and current.id == song.id:
            queue_state.remove_at_first(song)
        else:
            queue_state.remove(song)

        if song.fid is not None:
            self.__filesystem_service.delete_file(song.fid)

        self.__song_repository.delete(request.id)
