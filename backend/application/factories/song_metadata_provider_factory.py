from urllib.parse import urlparse

from backend.adapters.providers.youtube_song_metadata_provider import YoutubeSongMetadataProvider
from backend.application.errors.url_parse_error import UrlParseError
from backend.application.parsers.youtube_url_parser import YoutubeUrlParser
from backend.domain.providers.song_metadata_provider import SongMetadataProvider
from backend.service.dependency_injection import container


class SongMetadataProviderFactory:
    @staticmethod
    def create(url: str) -> SongMetadataProvider:
        if urlparse(url).hostname in YoutubeUrlParser.VALID_URLS:
            return container.resolve(YoutubeSongMetadataProvider)

        raise UrlParseError(url)
