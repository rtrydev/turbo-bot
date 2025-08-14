from dataclasses import dataclass


@dataclass
class SongDownloadDTO:
    id: str
    origin: str
