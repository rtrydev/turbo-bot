import tempfile
from typing import Generator

import discord

from backend.application.factories.audio_provider_factory import AudioProviderFactory
from backend.domain.models.song import Song
from backend.domain.providers.channel_connection_provider import ChannelConnectionProvider
from backend.domain.services.media_player_service import MediaPlayerService


class GeneratorAudioSource(discord.AudioSource):
    def __init__(self, byte_generator: Generator[bytes, None, None]):
        self.generator = byte_generator
        self.closed = False

    def read(self) -> bytes:
        try:
            return next(self.generator)
        except StopIteration:
            self.cleanup()
            return b""

    def is_opus(self) -> bool:
        return True

    def cleanup(self):
        self.closed = True

class DiscordMediaPlayerService(MediaPlayerService):
    __channel_connection_provider: ChannelConnectionProvider

    def __init__(self, channel_connection_provider: ChannelConnectionProvider) -> None:
        self.__channel_connection_provider = channel_connection_provider

    def play(self, song: Song) -> None:
        audio_provider = AudioProviderFactory.create_audio_provider(song)
        audio_stream = audio_provider.get_audio(song)

        if audio_stream is None:
            raise Exception(f'Audio stream for song {song.id} could not be created!')

        channel = self.__channel_connection_provider.get_channel_connection()
        stream = audio_provider.get_audio(song)

        temp_file = tempfile.NamedTemporaryFile(suffix='.opus', delete=False)

        for chunk in stream:
            temp_file.write(chunk)

        temp_file.flush()
        temp_file.seek(0)

        channel.play(discord.FFmpegOpusAudio(temp_file.name))

    def pause(self) -> None:
        channel = self.__channel_connection_provider.get_channel_connection()
        channel.pause()

    def stop(self) -> None:
        channel = self.__channel_connection_provider.get_channel_connection()
        channel.stop()
