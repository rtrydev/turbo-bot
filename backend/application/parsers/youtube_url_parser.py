from typing import Optional
from urllib.parse import urlparse, parse_qs
from backend.domain.parsers.url_parser import UrlParser


class YoutubeUrlParser(UrlParser):
    VALID_URLS = ['www.youtube.com', 'youtube.com', 'www.youtu.be', 'youtu.be']
    _url: str

    def __init__(self, url: str):
        self._url = url

    def get_id(self) -> Optional[str]:
        parsed_url = urlparse(self._url)

        if not parsed_url.hostname in self.VALID_URLS:
            return None

        query_params = parse_qs(parsed_url.query)
        video_id = query_params.get('v') or []

        if len(video_id) == 0:
            path_fragments = parsed_url.path.split('/')

            if len(path_fragments) < 2:
                return None

            return path_fragments[1]

        return video_id[0]
