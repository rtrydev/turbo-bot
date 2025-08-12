from abc import ABC, abstractmethod
from typing import Optional


class FilesystemService(ABC):
    @abstractmethod
    def save_file(self, descriptor: str, content: bytes) -> Optional[str]:
        pass

    @abstractmethod
    def get_file(self, descriptor: str) -> Optional[bytes]:
        pass
