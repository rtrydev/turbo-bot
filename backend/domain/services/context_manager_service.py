from abc import ABC, abstractmethod
from typing import Callable

from backend.domain.models.song import Song
from backend.domain.models.song_queue import SongQueue

#: Signature of a queue change listener (see :meth:`ContextManagerService.add_queue_listener`).
#: Called after every queue mutation (add, skip, clear, …) so live clients
#: can be notified of the new state. Must not block the mutation path.
QueueListener = Callable[[], None]


class ContextManagerService(ABC):
    @abstractmethod
    def get_queue_state(self) -> SongQueue:
        pass

    @abstractmethod
    def add_queue_listener(self, callback: QueueListener) -> None:
        """Register a callback fired after every queue mutation.

        The callback is invoked synchronously on the thread that performed
        the mutation, so it must be cheap and non-blocking (e.g. schedule
        work on an event loop and return). Exceptions raised by the callback
        are logged and swallowed — a broken listener must never break queue
        operations.
        """
        pass

    def remove_queue_listener(self, callback: QueueListener) -> None:
        """Unregister a previously added listener. No-op by default."""
        pass
