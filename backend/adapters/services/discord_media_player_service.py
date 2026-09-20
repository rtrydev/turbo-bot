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
        #: Path of the temp .opus file backing this source (if any); the
        #: owner unlinks it when the source is retired.
        self.temp_file_name: Optional[str] = None

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

    def play(self, song: Song) -> None:
        if not self._next_lock.acquire(blocking=False):
            return

        try:
            self._play_song(song, in_place=True)
        finally:
            self._next_lock.release()

    def _prepare_source(self, song: Song) -> WatchdogFFmpegOpusAudio:
        """Build the opus source for ``song``, downloading audio if needed.

        This is the slow part (seconds on an un-cached stream), and it runs
        while a *different* track is still playing on the channel, so it must
        not be confused with a stall of the current playback.
        """
        if song.fid is None:
            db_song = self.__song_repository.get_by_id(song.id)
            song.fid = db_song.fid

        audio_provider = AudioProviderFactory.create_audio_provider(song)
        audio_stream = audio_provider.get_audio(song)

        if audio_stream is None:
            raise Exception(f'Audio stream for song {song.id} could not be created!')

        temp_file = tempfile.NamedTemporaryFile(suffix='.opus', delete=False)
        temp_file_name = temp_file.name

        for chunk in audio_stream:
            temp_file.write(chunk)

        temp_file.flush()
        temp_file.close()

        source = WatchdogFFmpegOpusAudio(
            temp_file_name,
            options='-af loudnorm=I=-14:TP=-1.5:LRA=11'
        )
        source.temp_file_name = temp_file_name
        return source

    def _play_song(self, song: Song, *, in_place: bool) -> None:
        channel = self.__channel_connection_provider.get_channel_connection()

        if channel is None:
            raise Exception('No active voice channel to play into.')

        # Prepare *before* touching the channel: with ``in_place`` the current
        # track must keep playing (audibly) for the whole prep; otherwise we
        # would briefly silence a track the user asked to hear.
        source = self._prepare_source(song)

        def after_callback(error):
            if self._next_lock.acquire(blocking=False):
                try:
                    # The attached source just finished: free its temp file
                    # (its ffmpeg process already exited) before advancing.
                    self._release_channel_source()
                    self._advance()
                finally:
                    self._next_lock.release()

        playing = channel.is_playing() or channel.is_paused()

        if in_place and playing:
            # Keep the same AudioPlayer running: a source swap never creates
            # an "is not playing" gap on the channel, so the queue's
            # "now playing" slot (which mirrors the queue state, not the
            # channel flags) stays consistent with what is audible.
            old_source = channel.source
            channel.source = source
            # The old source will never be read again — retire it here, while
            # we still hold a reference to it (the channel no longer does).
            self._kill_source(old_source)
        else:
            # A genuine (re)start: with the AudioPlayer stopped, assigning
            # ``channel.source`` alone would start *nothing*, so this path
            # must go through channel.play(), which also registers the
            # advance callback for when this source finishes.
            if playing:
                self._kill_ffmpeg(channel)
                channel.stop()
            channel.play(source, after=after_callback)

        self._arm_watchdog()

    def pause(self) -> None:
        channel = self.__channel_connection_provider.get_channel_connection()
        if channel is None:
            raise Exception('No active voice channel to pause.')
        channel.pause()

    def resume(self) -> None:
        channel = self.__channel_connection_provider.get_channel_connection()
        if channel is None:
            raise Exception('No active voice channel to resume.')
        channel.resume()

    @staticmethod
    def _kill_ffmpeg(channel) -> None:
        DiscordMediaPlayerService._kill_source(channel.source)

    @staticmethod
    def _kill_source(source) -> None:
        """Stop a source's ffmpeg process and delete its temp .opus file."""
        if not isinstance(source, WatchdogFFmpegOpusAudio):
            return

        proc = source._process
        if proc is not None:
            if proc.poll() is None:
                proc.kill()
            # Wait for the handle to be released so the unlink below cannot
            # race with the still-open file.
            proc.wait()

        if source.temp_file_name is not None:
            try:
                os.unlink(source.temp_file_name)
            except OSError:
                pass

    def _release_channel_source(self) -> None:
        channel = self.__channel_connection_provider.get_channel_connection()
        if channel is not None:
            DiscordMediaPlayerService._kill_source(channel.source)

    def stop(self) -> None:
        channel = self.__channel_connection_provider.get_channel_connection()
        if channel is not None:
            self._kill_ffmpeg(channel)
            channel.stop()

    def next(self) -> None:
        if not self._next_lock.acquire(blocking=False):
            return

        try:
            self._advance()
        finally:
            self._next_lock.release()

    def _advance(self) -> None:
        """Move on from the finished/abandoned current track.

        Order matters: the slot is advanced *first*, while the channel still
        reports the finished track as playing — the slot mirrors the queue
        state, and the previous track is audibly gone the moment its source
        is swapped out. Swapping first would expose a gap where the channel
        reports "not playing" while the slot still points at the finished
        track, which the admin view would render as "nothing playing" even
        though music kept going.
        """
        channel = self.__channel_connection_provider.get_channel_connection()

        next_song = self.__context_manager_service.get_queue_state().get_next()

        if next_song:
            self._play_song(next_song, in_place=True)
            return

        if channel is not None and (channel.is_playing() or channel.is_paused()):
            self._kill_ffmpeg(channel)
            channel.stop()

    def _arm_watchdog(self) -> None:
        """Watch the *currently attached* source for a real stall.

        The check is scoped to the exact source instance that is playing:
        preparing the *next* track's source (download/decode can take
        seconds) never moves the current source's frame clock, and a source
        that is about to be swapped out — or already was — is never treated
        as the stale one. Without that scope the watchdog kills a healthy
        transition, which shows up as the channel going silent on every
        song change.
        """
        def watchdog():
            ch = self.__channel_connection_provider.get_channel_connection()
            if ch is None or not (ch.is_playing() or ch.is_paused()):
                return

            if ch.is_paused():
                self._arm_watchdog()
                return

            source = ch.source
            if isinstance(source, WatchdogFFmpegOpusAudio):
                if source.seconds_since_last_frame() > STALL_TIMEOUT:
                    self._kill_ffmpeg(ch)
                    ch.stop()
                    return

            self._arm_watchdog()

        threading.Timer(WATCHDOG_CHECK_INTERVAL, watchdog).start()

    def is_playing(self) -> bool:
        channel = self.__channel_connection_provider.get_channel_connection()
        return channel is not None and channel.is_playing()

    def is_paused(self) -> bool:
        channel = self.__channel_connection_provider.get_channel_connection()
        return channel is not None and channel.is_paused()
