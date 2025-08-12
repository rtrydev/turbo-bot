import os
import tempfile
from typing import Optional

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
                'extract_audio': True,
                'audio_format': 'mp3',
                'logtostderr': False,
                'force_overwrites': True,
                'prefer_ffmpeg': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(song.origin, download=True)
                filename = ydl.prepare_filename(info)
                mp3_path = os.path.splitext(filename)[0] + '.mp3'

            with open(mp3_path, 'rb') as f:
                audio_bytes = f.read()

            return self.__filesystem_service.save_file(song.id, audio_bytes)
