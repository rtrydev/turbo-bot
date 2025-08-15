from backend.domain.models.song_queue import SongQueue
from backend.domain.services.context_manager_service import ContextManagerService


class InMemoryContextManagerService(ContextManagerService):
    __queue_state: SongQueue

    def __init__(self) -> None:
        self.__queue_state = SongQueue.create()

    def get_queue_state(self) -> SongQueue:
        return self.__queue_state
