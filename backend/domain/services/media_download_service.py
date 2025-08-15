from abc import ABC, abstractmethod
from typing import Optional, Generator

from backend.domain.models.song import Song


class MediaDownloadService(ABC):
    @abstractmethod
    def download_song(self, song: Song) -> Optional[str]:
        pass

    @abstractmethod
    def get_audio_stream(self, song: Song) -> Generator[bytes, None, None]:
        pass
