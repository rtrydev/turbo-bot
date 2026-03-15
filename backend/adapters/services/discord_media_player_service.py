import os
import tempfile
import threading
import time
from typing import Generator, Optional

import discord

from backend.application.factories.audio_provider_factory import AudioProviderFactory
from backend.domain.models.song import Song
from backend.domain.providers.channel_connection_provider import ChannelConnectionProvider
from backend.domain.repositories.song_repository import SongRepository
from backend.domain.services.context_manager_service import ContextManagerService
from backend.domain.services.media_player_service import MediaPlayerService

STALL_TIMEOUT = 15
WATCHDOG_CHECK_INTERVAL = 10


class WatchdogFFmpegOpusAudio(discord.FFmpegOpusAudio):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._last_frame_time = time.monotonic()

    def read(self) -> bytes:
        data = super().read()
        if data:
            self._last_frame_time = time.monotonic()
        return data

    def seconds_since_last_frame(self) -> float:
        return time.monotonic() - self._last_frame_time


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
    __context_manager_service: ContextManagerService
    __song_repository: SongRepository

    def __init__(self, channel_connection_provider: ChannelConnectionProvider, context_manager_service: ContextManagerService, song_repository: SongRepository) -> None:
        self.__channel_connection_provider = channel_connection_provider
        self.__context_manager_service = context_manager_service
        self.__song_repository = song_repository
        self._next_lock = threading.Lock()
        self._current_playback_id = 0

    def play(self, song: Song) -> None:
        if song.fid is None:
            db_song = self.__song_repository.get_by_id(song.id)
            song.fid = db_song.fid

        audio_provider = AudioProviderFactory.create_audio_provider(song)
        audio_stream = audio_provider.get_audio(song)

        if audio_stream is None:
            raise Exception(f'Audio stream for song {song.id} could not be created!')

        channel = self.__channel_connection_provider.get_channel_connection()

        self._current_playback_id += 1
        my_playback_id = self._current_playback_id

        temp_file = tempfile.NamedTemporaryFile(suffix='.opus', delete=False)
        temp_file_name = temp_file.name

        for chunk in audio_stream:
            temp_file.write(chunk)

        temp_file.flush()
        temp_file.close()

        watchdog_timer: list[Optional[threading.Timer]] = [None]

        def after_callback(error):
            if watchdog_timer[0] is not None:
                watchdog_timer[0].cancel()
            try:
                os.unlink(temp_file_name)
            except OSError:
                pass

            if self._current_playback_id == my_playback_id:
                self.next()

        source = WatchdogFFmpegOpusAudio(temp_file_name)
        channel.play(source, after=after_callback)

        def watchdog():
            ch = self.__channel_connection_provider.get_channel_connection()
            if ch is None or not (ch.is_playing() or ch.is_paused()):
                return

            if ch.is_paused():
                watchdog_timer[0] = threading.Timer(WATCHDOG_CHECK_INTERVAL, watchdog)
                watchdog_timer[0].start()
                return

            if isinstance(ch.source, WatchdogFFmpegOpusAudio):
                if ch.source.seconds_since_last_frame() > STALL_TIMEOUT:
                    self._kill_ffmpeg(ch)
                    ch.stop()
                    return

            watchdog_timer[0] = threading.Timer(WATCHDOG_CHECK_INTERVAL, watchdog)
            watchdog_timer[0].start()

        watchdog_timer[0] = threading.Timer(WATCHDOG_CHECK_INTERVAL, watchdog)
        watchdog_timer[0].start()

    def pause(self) -> None:
        channel = self.__channel_connection_provider.get_channel_connection()
        channel.pause()

    def resume(self) -> None:
        channel = self.__channel_connection_provider.get_channel_connection()
        channel.resume()

    @staticmethod
    def _kill_ffmpeg(channel) -> None:
        source = channel.source
        if isinstance(source, WatchdogFFmpegOpusAudio):
            proc = source._process
            if proc is not None and proc.poll() is None:
                proc.kill()

    def stop(self) -> None:
        channel = self.__channel_connection_provider.get_channel_connection()
        if channel is not None:
            self._kill_ffmpeg(channel)
        channel.stop()

    def next(self) -> None:
        if not self._next_lock.acquire(blocking=False):
            return

        try:
            channel = self.__channel_connection_provider.get_channel_connection()

            if channel is not None and (channel.is_playing() or channel.is_paused()):
                self._kill_ffmpeg(channel)
                channel.stop()

            next_song = self.__context_manager_service.get_queue_state().get_next()

            if next_song:
                self.play(next_song)
        finally:
            self._next_lock.release()
