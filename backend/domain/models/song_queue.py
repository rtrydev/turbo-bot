from typing import Optional
import random

from backend.domain.models.song import Song


class SongQueue:
    __songs: list[Song]
    __last_song: Optional[Song] = None
    __repeat: bool = False

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
        if self.__repeat and self.__last_song is not None:
            return self.__last_song

        if len(self.__songs) == 0:
            return None

        self.__last_song = self.__songs.pop(0)

        return self.__last_song

    def get_all(self) -> list[Song]:
        return self.__songs

    def clear(self) -> None:
        self.__songs = []

    def shuffle(self) -> None:
        random.shuffle(self.__songs)

    def toggle_repeat(self) -> None:
        self.__repeat = not self.__repeat
