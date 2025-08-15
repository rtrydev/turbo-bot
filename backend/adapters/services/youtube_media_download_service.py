import os
import subprocess
import tempfile
from typing import Optional, Generator

import yt_dlp

from backend.domain.models.song import Song
from backend.domain.services.filesystem_service import FilesystemService
from backend.domain.services.media_download_service import MediaDownloadService


class YoutubeMediaDownloadService(MediaDownloadService):
    __filesystem_service: FilesystemService

    def __init__(self, filesystem_service: FilesystemService) -> None:
        self.__filesystem_service = filesystem_service

    def download_song(self, song: Song) -> Optional[str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path_template = os.path.join(tmp_dir, '%(id)s.%(ext)s')

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': tmp_path_template,
                'quiet': True,
                'no_warnings': True,
                'logtostderr': False,
                'force_overwrites': True,
                'prefer_ffmpeg': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'opus',
                    'preferredquality': '192'
                }],
                'postprocessor_args': [
                    '-ar', '48000',
                    '-ac', '2',
                    '-f', 'opus'
                ]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(song.origin, download=True)
                filename = ydl.prepare_filename(info)
                opus_path = os.path.splitext(filename)[0] + '.opus'

            with open(opus_path, 'rb') as f:
                audio_bytes = f.read()

            return self.__filesystem_service.save_file(song.id, audio_bytes)

    def get_audio_stream(self, song: Song) -> Generator[bytes, None, None]:
        process = subprocess.Popen(
            [
                'yt-dlp',
                '-f', 'bestaudio',
                '-o', '-',
                song.origin
            ],
            stdout=subprocess.PIPE
        )

        ffmpeg_process = subprocess.Popen(
            [
                'ffmpeg',
                '-i', 'pipe:0',
                '-f', 'opus',
                '-ar', '48000',
                '-ac', '2',
                'pipe:1'
            ],
            stdin=process.stdout,
            stdout=subprocess.PIPE
        )

        if not ffmpeg_process.stdout:
            return

        for chunk in iter(lambda: ffmpeg_process.stdout.read(3840), b''):
            yield chunk

        process.stdout.close()
        process.wait()
