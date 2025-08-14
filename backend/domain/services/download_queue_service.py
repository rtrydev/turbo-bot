from abc import ABC, abstractmethod
from typing import Callable


class DownloadQueueService(ABC):
    @abstractmethod
    def register_message_observer(self, callback: Callable) -> None:
        pass

    @abstractmethod
    def send_message(self, message: str) -> None:
        pass
