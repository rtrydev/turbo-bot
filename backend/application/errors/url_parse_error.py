class UrlParseError(Exception):
    def __init__(self, url: str):
        super().__init__(f'Failed to parse {url}!')
