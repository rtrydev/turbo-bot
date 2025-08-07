from typing import Optional

from backend.domain.models.song import Song
from backend.domain.repositories.song_repository import SongRepository


class InMemorySongRepository(SongRepository):
    __store: list[Song]

    def __init__(self):
        self.__store = []

    def create(self, song: Song) -> None:
        self.__store.append(song)

    def get_by_id(self, _id: str) -> Optional[Song]:
        try:
            return next(
                song
                for song in self.__store
                if song.id == _id
            )
        except StopIteration:
            return None
