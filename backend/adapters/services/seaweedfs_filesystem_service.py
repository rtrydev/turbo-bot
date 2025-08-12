from typing import Optional

from backend.domain.services.filesystem_service import FilesystemService
from pyseaweed import WeedFS


class SeaweedfsFilesystemService(FilesystemService):
    def __init__(self, master_address: str, master_port: int):
        self.client = WeedFS(master_address, master_port)

    def save_file(self, descriptor: str, content: bytes) -> Optional[str]:
        return self.client.upload_file(None, content, descriptor)

    def get_file(self, descriptor: str) -> Optional[bytes]:
        return self.client.get_file(descriptor)
