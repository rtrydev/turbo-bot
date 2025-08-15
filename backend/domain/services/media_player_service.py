from abc import ABC, abstractmethod

from backend.domain.models.song import Song


class MediaPlayerService(ABC):
    @abstractmethod
    def play(self, song: Song) -> None:
        pass

    @abstractmethod
    def pause(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass
