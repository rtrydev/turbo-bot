from abc import ABC, abstractmethod

from backend.domain.models.song_queue import SongQueue


class ContextManagerService(ABC):
    @abstractmethod
    def get_queue_state(self) -> SongQueue:
        pass
