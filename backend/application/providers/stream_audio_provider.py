from typing import Generator

from backend.domain.models.song import Song
from backend.domain.providers.audio_provider import AudioProvider
from backend.domain.services.media_download_service import MediaDownloadService


class StreamAudioProvider(AudioProvider):
    __media_download_service: MediaDownloadService

    def __init__(self, media_download_service: MediaDownloadService) -> None:
        self.__media_download_service = media_download_service

    def get_audio(self, song: Song) -> Generator[bytes, None, None]:
        audio_stream = self.__media_download_service.get_audio_stream(song)

        if audio_stream is None:
            raise Exception(f'Audio stream for song {song.id} could not be created!')

        yield from audio_stream
