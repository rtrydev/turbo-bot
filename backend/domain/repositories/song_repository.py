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

    @abstractmethod
    def delete(self, _id: str) -> bool:
        pass

    @abstractmethod
    def get_random(self, count: int) -> list[Song]:
        pass

    @abstractmethod
    def find(self, query: str = '', page: int = 0, limit: int = 25) -> tuple[list[Song], int]:
        pass