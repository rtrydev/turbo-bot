from dataclasses import dataclass
from typing import Optional

from backend.application.dtos.admin_dto import QueueStateDTO
from backend.application.dtos.song_dto import SongDTO
from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.services.context_manager_service import ContextManagerService
from backend.domain.services.media_player_service import MediaPlayerService


def _song_dto(song) -> SongDTO:
    return SongDTO(id=song.id, title=song.title, length=song.length, origin=song.origin)


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
        player = self.__media_player_service

        # The "now playing" slot mirrors what the player actually has loaded,
        # and only while audio is alive in the channel. Once playback stops
        # (song finished, channel left, bot stopped) the slot is empty even
        # if a track was the last one advanced — the UI then shows a stopped
        # state, not a ghost of a track that is no longer playing.
        currently_playing = None
        if player.is_playing() or player.is_paused():
            last_song = queue.get_last_song()
            currently_playing = _song_dto(last_song) if last_song else None

        return QueueStateDTO(
            songs=[_song_dto(s) for s in queue.get_all()],
            currently_playing=currently_playing,
            is_playing=player.is_playing(),
            is_paused=player.is_paused(),
            repeat_enabled=queue.is_repeat_enabled()
        )
