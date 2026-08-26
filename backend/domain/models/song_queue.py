from __future__ import annotations

import threading
from typing import Optional
import random

from backend.domain.models.song import Song


class SongQueue:
    """The ordered list of tracks queued for playback.

    The queue is mutated from several places at once — the REST API
    (add / add-random / clear / skip), the Discord bot (advancing to the
    next track) and the download worker. All of those share the *same*
    ``SongQueue`` instance, so every mutating operation is serialized
    through a single re-entrant lock. Without it, concurrent random adds
    could interleave with a queue advance and a song could end up enqueued
    twice (or skipped), which shows up in the admin UI as duplicate rows
    and "missing" tracks until the next full refresh.
    """

    __songs: list[Song]
    __last_song: Optional[Song] = None
    __repeat: bool = False
    __lock: threading.RLock = threading.RLock()

    def __init__(self, songs: list[Song]) -> None:
        self.__songs = songs

    @staticmethod
    def create(songs: Optional[list[Song]] = None) -> 'SongQueue':
        if songs is None:
            return SongQueue([])

        return SongQueue(songs)

    def add(self, song: Song) -> None:
        with self.__lock:
            self.__songs.append(song)

    def get_next(self) -> Optional[Song]:
        with self.__lock:
            if self.__repeat and self.__last_song is not None:
                return self.__last_song

            if len(self.__songs) == 0:
                return None

            self.__last_song = self.__songs.pop(0)

            return self.__last_song

    def get_all(self) -> list[Song]:
        """Return a snapshot of the current queue.

        The snapshot is taken atomically under the mutation lock so the
        caller never observes a half-mutated list, and it is deduplicated
        as a safety net for any stale entries that predate this guard.
        """
        with self.__lock:
            songs = list(self.__songs)
            seen: set[str] = set()
            deduped: list[Song] = []
            for song in songs:
                if song.id in seen:
                    continue
                seen.add(song.id)
                deduped.append(song)
            return deduped

    def clear(self) -> None:
        with self.__lock:
            self.__songs = []

    def shuffle(self) -> None:
        with self.__lock:
            random.shuffle(self.__songs)

    def toggle_repeat(self) -> None:
        with self.__lock:
            self.__repeat = not self.__repeat

    def skip(self) -> None:
        with self.__lock:
            self.__last_song = None

    def get_last_song(self) -> Optional[Song]:
        with self.__lock:
            return self.__last_song

    def is_repeat_enabled(self) -> bool:
        with self.__lock:
            return self.__repeat

    def remove_at(self, index: int) -> Optional[Song]:
        with self.__lock:
            if 0 <= index < len(self.__songs):
                return self.__songs.pop(index)
            return None

    def remove(self, song: Song) -> None:
        with self.__lock:
            self.__songs = [s for s in self.__songs if s.id != song.id]

    def move(self, from_index: int, to_index: int) -> None:
        with self.__lock:
            if 0 <= from_index < len(self.__songs) and 0 <= to_index < len(self.__songs):
                song = self.__songs.pop(from_index)
                self.__songs.insert(to_index, song)

    def __len__(self) -> int:
        with self.__lock:
            return len(self.__songs)
