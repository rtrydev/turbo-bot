from yt_dlp import YoutubeDL

from backend.domain.models.song_metadata import SongMetadata
from backend.domain.providers.song_metadata_provider import SongMetadataProvider
from backend.domain.repositories.song_repository import SongRepository


class YoutubeSongMetadataProvider(SongMetadataProvider):
    __song_repository: SongRepository

    def __init__(self, song_repository: SongRepository):
        self.__song_repository = song_repository

    def get_meta(self, _id: str) -> SongMetadata:
        existing_song = self.__song_repository.get_by_id(_id)

        if existing_song is not None:
            return existing_song

        with YoutubeDL() as yt_dl:
            meta = yt_dl.extract_info(_id, False)

            return SongMetadata(
                title=meta.get('title'),
                length=meta.get('duration')
            )
