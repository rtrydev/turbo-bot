from abc import ABC, abstractmethod
from typing import Optional

from backend.domain.models.song import Song


class SongRepository(ABC):
    @abstractmethod
    def create(self, song: Song) -> None:
        pass

    @abstractmethod
    def get_by_id(self, _id: str) -> Optional[Song]:
        pass

    @abstractmethod
    def update(self, song: Song) -> None:
        pass