from abc import ABC, abstractmethod

from backend.domain.models.song_metadata import SongMetadata


class SongMetadataProvider(ABC):
    @abstractmethod
    def get_meta(self, _id: str) -> SongMetadata:
        pass
