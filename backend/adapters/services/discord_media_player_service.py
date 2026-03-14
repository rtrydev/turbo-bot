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

# How long without any audio frame (while not paused) before we consider ffmpeg hung.
STALL_TIMEOUT = 30  # seconds
# How often the watchdog re-checks playback health.
WATCHDOG_CHECK_INTERVAL = 10  # seconds


class WatchdogFFmpegOpusAudio(discord.FFmpegOpusAudio):
    """FFmpegOpusAudio that records when the last non-empty frame was produced.

    The watchdog uses this to distinguish a hung ffmpeg process (no frames for
    STALL_TIMEOUT seconds while the channel is actively playing) from a legitimately
    long track that is producing audio normally.
    """

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
            # Only advance to next song if this callback belongs to the current playback.
            # When next() calls channel.stop() the after callback fires from the audio
            # thread; the playback ID will have been superseded by then, so we skip it.
            if self._current_playback_id == my_playback_id:
                self.next()

        source = WatchdogFFmpegOpusAudio(temp_file_name)
        channel.play(source, after=after_callback)

        def watchdog():
            ch = self.__channel_connection_provider.get_channel_connection()
            if ch is None or not (ch.is_playing() or ch.is_paused()):
                return

            if ch.is_paused():
                # No frames expected while paused; check again later.
                watchdog_timer[0] = threading.Timer(WATCHDOG_CHECK_INTERVAL, watchdog)
                watchdog_timer[0].start()
                return

            if isinstance(ch.source, WatchdogFFmpegOpusAudio):
                if ch.source.seconds_since_last_frame() > STALL_TIMEOUT:
                    # ffmpeg is stuck — kill the process to unblock the audio
                    # thread (which is blocked on stdout.read), then stop.
                    proc = ch.source._process
                    if proc is not None and proc.poll() is None:
                        proc.kill()
                    ch.stop()
                    return

            # Still healthy; reschedule.
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

    def stop(self) -> None:
        channel = self.__channel_connection_provider.get_channel_connection()
        channel.stop()

    def next(self) -> None:
        # Prevent concurrent calls: the after callback fires from the audio thread
        # at the same time next() may be running from a command handler thread.
        # A non-blocking acquire drops the redundant call instead of queuing it.
        if not self._next_lock.acquire(blocking=False):
            return

        try:
            channel = self.__channel_connection_provider.get_channel_connection()

            if channel is not None and (channel.is_playing() or channel.is_paused()):
                channel.stop()

            next_song = self.__context_manager_service.get_queue_state().get_next()

            if next_song:
                self.play(next_song)
        finally:
            self._next_lock.release()
