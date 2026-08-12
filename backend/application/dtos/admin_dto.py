from dataclasses import dataclass

from backend.application.dtos.song_dto import SongDTO


@dataclass
class QueueStateDTO:
    songs: list[SongDTO]
    currently_playing: SongDTO | None
    is_playing: bool
    is_paused: bool
    repeat_enabled: bool


@dataclass
class SongsListResponseDTO:
    songs: list[SongDTO]
    total: int
    page: int
    limit: int
