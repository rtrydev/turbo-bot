from dataclasses import dataclass
from typing import Optional

from backend.application.dtos.admin_dto import QueueStateDTO
from backend.application.dtos.song_dto import SongDTO
from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.services.context_manager_service import ContextManagerService
from backend.domain.services.media_player_service import MediaPlayerService


@dataclass
class GetQueueStateQuery(Request[Optional[QueueStateDTO]]):
    pass


class GetQueueStateQueryHandler(RequestHandler[GetQueueStateQuery, Optional[QueueStateDTO]]):
    __context_manager_service: ContextManagerService
    __media_player_service: MediaPlayerService

    def __init__(self, context_manager_service: ContextManagerService, media_player_service: MediaPlayerService) -> None:
        self.__context_manager_service = context_manager_service
        self.__media_player_service = media_player_service

    def handle(self, request: GetQueueStateQuery) -> Optional[QueueStateDTO]:
        queue = self.__context_manager_service.get_queue_state()
        current_song = self.__media_player_service.get_current_song()

        return QueueStateDTO(
            songs=[SongDTO(id=s.id, title=s.title, length=s.length, origin=s.origin) for s in queue.get_all()],
            currently_playing=SongDTO(id=current_song.id, title=current_song.title, length=current_song.length, origin=current_song.origin) if current_song else None,
            is_playing=self.__media_player_service.is_playing(),
            is_paused=self.__media_player_service.is_paused(),
            repeat_enabled=queue.is_repeat_enabled()
        )
