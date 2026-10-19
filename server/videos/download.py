from pathlib import Path
from typing import Callable, Dict

import yt_dlp

from .video import VideoSource
import utils

diag = utils.gen_diag("download")


def download_youtube(video_id: str, dest_stem: Path) -> Path:
    """
    Downloads audio from YouTube using yt-dlp to <dest_stem>.mp3.
    Returns the path yt-dlp actually wrote, raises on failure.
    """
    ydl_opts = {
        'format': 'ba/b',
        'extractor_args': {
            'youtube': {
                'player_client': ['web_embedded', 'android'],
            },
        },
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'outtmpl': f"{dest_stem}.%(ext)s",
        # Audio is shared per video_id and replaced on every request
        'overwrites': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_id, download=True)
    # TODO: check for 403 and return error; also check for unknown errors
    # TODO: make sure this download doesn't hang.
    # TODO: add progress hooks
    # TODO: look into supporting bgutil_ytdlp_pot_provider

    downloads = (info or {}).get("requested_downloads") or []
    if not downloads or not downloads[0].get("filepath"):
        raise RuntimeError(f"yt-dlp did not report an output file for {video_id}")
    return Path(downloads[0]["filepath"])


_DOWNLOADERS: Dict[VideoSource, Callable[[str, Path], Path]] = {
    VideoSource.YOUTUBE: download_youtube,
}


def download_audio(video_id: str, source: VideoSource, dest_stem: Path) -> Path:
    """
    Downloads audio for a video from the given source to <dest_stem>.<ext>.
    Returns the path of the downloaded file; raises on failure.
    """
    source = VideoSource(source)
    download_fn = _DOWNLOADERS.get(source)
    if download_fn is None:
        raise ValueError(f"No downloader registered for source {source.value}")

    diag.info(f"download_audio: Downloading {source.value}:{video_id} to {dest_stem}.*")
    return download_fn(video_id, dest_stem)

