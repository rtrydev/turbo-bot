from urllib.parse import urlparse

from backend.application.errors.url_parse_error import UrlParseError
from backend.application.parsers.youtube_url_parser import YoutubeUrlParser
from backend.domain.parsers.url_parser import UrlParser


class UrlParserFactory:
    @staticmethod
    def create(url: str) -> UrlParser:
        if urlparse(url).hostname in YoutubeUrlParser.VALID_URLS:
            return YoutubeUrlParser(url)

        raise UrlParseError(url)
