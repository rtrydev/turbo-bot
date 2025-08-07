from typing import Optional
import random

from backend.domain.models.song import Song


class SongQueue:
    __songs: list[Song]

    def __init__(self, songs: list[Song]) -> None:
        self.__songs = songs

    @staticmethod
    def create(songs: Optional[list[Song]] = None) -> 'SongQueue':
        if songs is None:
            return SongQueue([])

        return SongQueue(songs)

    def add(self, song: Song) -> None:
        self.__songs.append(song)

    def get_next(self) -> Optional[Song]:
        if len(self.__songs) == 0:
            return None

        return self.__songs.pop(0)

    def get_all(self) -> list[Song]:
        return self.__songs

    def clear(self) -> None:
        self.__songs = []

    def shuffle(self) -> None:
        random.shuffle(self.__songs)
