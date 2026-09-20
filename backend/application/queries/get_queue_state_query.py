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

        # The "now playing" slot is authoritative while a session is running:
        # the player advances the slot *first* and then swaps the channel's
        # source in place, so between the two the slot already points at the
        # next track — the one about to play — and that must be what the UI
        # shows (mirroring what is about to be audible, never a gap).
        #
        # The slot is only discarded on a *genuine* stop — the queue is
        # empty and nothing is playing or paused (a session truly over).
        # During a transition the queue still holds tracks, so the slot
        # survives; and every stop path that empties the slot also empties
        # the queue, so a stale ghost cannot outlive the session that played
        # it.
        currently_playing = None
        if not queue.get_all() and not (player.is_playing() or player.is_paused()):
            currently_playing = None
        else:
            last_song = queue.get_last_song()
            currently_playing = _song_dto(last_song) if last_song else None

        return QueueStateDTO(
            songs=[_song_dto(s) for s in queue.get_all()],
            currently_playing=currently_playing,
            is_playing=player.is_playing(),
            is_paused=player.is_paused(),
            repeat_enabled=queue.is_repeat_enabled()
        )
