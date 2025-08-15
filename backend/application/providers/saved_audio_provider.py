from typing import Generator

from backend.domain.models.song import Song
from backend.domain.providers.audio_provider import AudioProvider
from backend.domain.services.filesystem_service import FilesystemService


class SavedAudioProvider(AudioProvider):
    __filesystem_service: FilesystemService

    def __init__(self, filesystem_service: FilesystemService) -> None:
        self.__filesystem_service = filesystem_service

    def get_audio(self, song: Song) -> Generator[bytes, None, None]:
        audio_bytes = self.__filesystem_service.get_file(song.fid)

        if audio_bytes is None:
            raise FileNotFoundError(f'Audio file for song {song.id} not found.')

        yield audio_bytes