from backend.domain.errors.permanent_error import PermanentError


class SongAlreadyDownloadedError(PermanentError):
    def __init__(self, _id: str):
        super().__init__(f'Song with id {_id} has already been downloaded!')
