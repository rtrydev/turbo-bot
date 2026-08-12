from dataclasses import dataclass


@dataclass
class SongDTO:
    id: str
    title: str
    length: int
    origin: str
