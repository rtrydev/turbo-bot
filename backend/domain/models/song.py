from dataclasses import dataclass

from backend.domain.models.song_metadata import SongMetadata


@dataclass
class Song(SongMetadata):
    id: str
    origin: str
