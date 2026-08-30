import logging
import threading

from backend.domain.models.song_queue import SongQueue
from backend.domain.services.context_manager_service import ContextManagerService, QueueListener

logger = logging.getLogger(__name__)


class InMemoryContextManagerService(ContextManagerService):
    __queue_state: SongQueue
    __listeners: list[QueueListener]
    __listeners_lock: threading.Lock

    def __init__(self) -> None:
        self.__queue_state = SongQueue.create()
        self.__listeners = []
        self.__listeners_lock = threading.Lock()
        self.__queue_state.add_observer(self.__notify_listeners)

    def get_queue_state(self) -> SongQueue:
        return self.__queue_state

    def add_queue_listener(self, callback: QueueListener) -> None:
        with self.__listeners_lock:
            if callback in self.__listeners:
                return
            self.__listeners.append(callback)

    def remove_queue_listener(self, callback: QueueListener) -> None:
        with self.__listeners_lock:
            self.__listeners = [l for l in self.__listeners if l is not callback]

    def __notify_listeners(self) -> None:
        """Fan out a queue-change event to every registered listener.

        Runs on whichever thread mutated the queue (an aiohttp handler, a
        Discord command, the player thread). A listener must therefore be
        cheap and thread-safe — the API port uses
        ``run_coroutine_threadsafe`` to hop onto its event loop. Errors are
        logged and swallowed so a broken listener never breaks playback.
        """
        with self.__listeners_lock:
            listeners = list(self.__listeners)
        for listener in listeners:
            try:
                listener()
            except Exception as exc:  # noqa: BLE001 - intentional broad catch
                logger.debug('queue listener failed: %s', exc)

    def __publish_now_playing(self) -> None:
        """Re-emit queue change events while the observed "now playing"
        slot has not settled.

        A single observer notification is not enough for an *advance*: the
        queue mutation only records the slot *after* the media player has
        already loaded the new track — the transition window (the previous
        audio is still alive on the channel for a moment after the slot
        moved) is real and lasts however long the next audio setup takes,
        so a snapshot taken inside that window can be observed as a full
        event.

        Re-notifying until the slot *and* the player state stabilize keeps
        the pushed events consistent with each other: no event reports a
        stale or missing "now playing" while audio is still alive.
        """
        queue = self.__queue_state
        for _ in range(3):
            with self.__listeners_lock:
                listeners = list(self.__listeners)
            if not listeners:
                return
            for listener in listeners:
                try:
                    listener()
                except Exception as exc:  # noqa: BLE001 - same as __notify_listeners
                    logger.debug('queue listener failed: %s', exc)
            if not queue.get_all() and queue.get_last_song() is None:
                break
