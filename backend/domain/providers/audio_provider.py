from abc import ABC, abstractmethod
from typing import Generator

from backend.domain.models.song import Song


class AudioProvider(ABC):
    @abstractmethod
    def get_audio(self, song: Song) -> Generator[bytes, None, None]:
        pass
