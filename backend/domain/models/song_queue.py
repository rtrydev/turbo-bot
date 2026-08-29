from __future__ import annotations

import threading
from typing import Callable, Optional
import random

from backend.domain.models.song import Song

#: Signature of a queue change observer. Invoked (synchronously, on the
#: mutating thread) after every state change: add, get_next (advance),
#: clear, skip, remove, move, shuffle, repeat toggle.
QueueObserver = Callable[[], None]


class SongQueue:
    """The ordered list of tracks queued for playback.

    The queue is mutated from several places at once — the REST API
    (add / add-random / clear / skip), the Discord bot (advancing to the
    next track) and the download worker. All of those share the *same*
    ``SongQueue`` instance, so every mutating operation is serialized
    through a single re-entrant lock. Without it, concurrent operations
    could interleave with a queue advance and corrupt the list (a song
    skipped, or the same entry appended twice), which shows up in the
    admin UI as duplicate rows and "missing" tracks until the next full
    refresh.

    The lock guards against *torn* mutations only. It deliberately does
    not remove duplicates: a track that the user genuinely added twice is
    a real two-entry queue and must be preserved as-is.

    Every mutation also fires the registered :data:`QueueObserver`
    callbacks, so long-lived listeners (the websocket hub) are told the
    moment state changes — even for advances that originate inside the
    audio player (song finished) where no API handler is involved.
    """

    __songs: list[Song]
    __last_song: Optional[Song] = None
    __repeat: bool = False
    __last_skipped: Optional[Song] = None
    __lock: threading.RLock = threading.RLock()
    __observers: list[QueueObserver]
    __observers_lock: threading.Lock

    def __init__(self, songs: list[Song]) -> None:
        self.__songs = songs
        self.__observers = []
        self.__observers_lock = threading.Lock()

    @staticmethod
    def create(songs: Optional[list[Song]] = None) -> 'SongQueue':
        if songs is None:
            return SongQueue([])

        return SongQueue(songs)

    # --- observation -------------------------------------------------------

    def add_observer(self, callback: QueueObserver) -> None:
        with self.__observers_lock:
            if callback not in self.__observers:
                self.__observers.append(callback)

    def remove_observer(self, callback: QueueObserver) -> None:
        with self.__observers_lock:
            self.__observers = [c for c in self.__observers if c is not callback]

    def _notify_observers(self) -> None:
        with self.__observers_lock:
            observers = list(self.__observers)
        for observer in observers:
            try:
                observer()
            except Exception:  # noqa: BLE001 - a broken observer must not break playback
                pass

    # --- mutations ---------------------------------------------------------

    def add(self, song: Song) -> None:
        with self.__lock:
            self.__songs.append(song)
            self._notify_observers()

    def get_next(self) -> Optional[Song]:
        with self.__lock:
            if self.__repeat and self.__last_song is not None and self.__last_song is not self.__last_skipped:
                self._notify_observers()
                return self.__last_song

            if len(self.__songs) == 0:
                return None

            self.__last_song = self.__songs.pop(0)
            self._notify_observers()

            return self.__last_song

    def clear(self) -> None:
        with self.__lock:
            self.__songs = []
            self._notify_observers()

    def shuffle(self) -> None:
        with self.__lock:
            random.shuffle(self.__songs)
            self._notify_observers()

    def toggle_repeat(self) -> None:
        with self.__lock:
            self.__repeat = not self.__repeat
            self._notify_observers()

    def skip(self) -> None:
        with self.__lock:
            self.__last_song = None
            self._notify_observers()

    def skip_excluding(self, song: Optional[Song]) -> None:
        """Mark ``song`` as skipped so repeat mode does not re-play it.

        Called right before advancing, i.e. while ``song`` is still the
        current track. A subsequent manual skip resets the exclusion so the
        most recent skip wins.
        """
        with self.__lock:
            self.__last_skipped = song
            self._notify_observers()

    def reset_current(self) -> None:
        """Forget the current track entirely (e.g. when leaving a channel).

        Distinct from :meth:`skip`: nothing is being advanced to here, and
        the "now playing" slot is emptied rather than replaced.
        """
        with self.__lock:
            self.__last_song = None
            self.__last_skipped = None
            self._notify_observers()

    def remove_at(self, index: int) -> Optional[Song]:
        with self.__lock:
            if 0 <= index < len(self.__songs):
                removed = self.__songs.pop(index)
                self._notify_observers()
                return removed
            return None

    def remove(self, song: Song) -> None:
        with self.__lock:
            self.__songs = [s for s in self.__songs if s.id != song.id]
            self._notify_observers()

    def remove_at_first(self, song: Song) -> None:
        """Remove only the first occurrence of ``song`` (used to keep a
        queued copy of the currently playing track while dropping extras)."""
        with self.__lock:
            for i, s in enumerate(self.__songs):
                if s.id == song.id:
                    self.__songs.pop(i)
                    break
            self._notify_observers()

    def move(self, from_index: int, to_index: int) -> None:
        with self.__lock:
            if 0 <= from_index < len(self.__songs) and 0 <= to_index < len(self.__songs):
                song = self.__songs.pop(from_index)
                self.__songs.insert(to_index, song)
                self._notify_observers()

    # --- queries -----------------------------------------------------------

    def get_all(self) -> list[Song]:
        """Return a snapshot of the current queue.

        The snapshot is taken atomically under the mutation lock so the
        caller never observes a half-mutated list. Note this preserves
        genuine duplicates (a track legitimately added twice) — it only
        guards against *torn* reads, not against repeated entries.
        """
        with self.__lock:
            return list(self.__songs)

    def get_last_song(self) -> Optional[Song]:
        with self.__lock:
            return self.__last_song

    def is_repeat_enabled(self) -> bool:
        with self.__lock:
            return self.__repeat

    def __len__(self) -> int:
        with self.__lock:
            return len(self.__songs)
