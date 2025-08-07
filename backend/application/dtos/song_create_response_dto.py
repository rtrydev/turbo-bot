from dataclasses import dataclass


@dataclass
class SongCreateResponseDTO:
    id: str
    title: str
    length: int
    origin: str
