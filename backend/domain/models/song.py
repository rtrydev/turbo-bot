from dataclasses import dataclass
from typing import Optional

from backend.domain.models.song_metadata import SongMetadata


@dataclass
class Song(SongMetadata):
    id: str
    fid: Optional[str]
    origin: str
