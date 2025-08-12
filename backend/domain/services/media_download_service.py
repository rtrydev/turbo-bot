from abc import ABC, abstractmethod
from typing import Optional

from backend.domain.models.song import Song


class MediaDownloadService(ABC):
    @abstractmethod
    def download_song(self, song: Song) -> Optional[str]:
        pass
