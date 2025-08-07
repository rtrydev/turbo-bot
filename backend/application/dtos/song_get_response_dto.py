from dataclasses import dataclass


@dataclass
class SongGetResponseDTO:
    id: str
    title: str
    length: int
    origin: str
