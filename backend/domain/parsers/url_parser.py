from abc import ABC, abstractmethod
from typing import Optional


class UrlParser(ABC):
    @abstractmethod
    def get_id(self) -> Optional[str]:
        pass
