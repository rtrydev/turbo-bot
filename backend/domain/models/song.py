from dataclasses import dataclass


@dataclass
class Song:
    id: str
    title: str
    length: int
    origin: str
