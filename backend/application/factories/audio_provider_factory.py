from backend.application.providers.saved_audio_provider import SavedAudioProvider
from backend.application.providers.stream_audio_provider import StreamAudioProvider
from backend.domain.models.song import Song
from backend.domain.providers.audio_provider import AudioProvider
from backend.service.dependency_injection import container


class AudioProviderFactory:
    @staticmethod
    def create_audio_provider(song: Song) -> AudioProvider:
        if song.fid is not None:
            return container.resolve(SavedAudioProvider)

        return container.resolve(StreamAudioProvider)
