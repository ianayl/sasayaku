import yt_dlp
from pathlib import Path
from typing import Optional, Dict
from utils.config import CONFIG
from .video import VideoSource
import utils

diag = utils.gen_diag("download")

def download_youtube(video_id: str, tmp_download_path: Path) -> None:
    """Downloads a video from YouTube using yt-dlp."""
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
        'outtmpl': str(tmp_download_path),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_id])
    # TODO: check for 403 and return error; also check for unknown errors
    # TODO: make sure this download doesn't hang. 
    # TODO: add progress hooks
    # TODO: look into supporting bgutil_ytdlp_pot_provider


def download_video(video_id: str, source: VideoSource) -> Optional[Path]:
    """
    Downloads a video from the specified source. Returns a path to the 
    downloaded .mp3 file if success, or None if failed.
    """
    # Path construction: <base_path>/<source_name>/<video_id>/<video_id>-7.mp3
    base_path = Path(CONFIG("downloads.downloads_path"))
    download_dir = base_path / source.value / video_id
    download_dir.mkdir(parents=True, exist_ok=True)
    tmp_download_path = download_dir / f"{video_id}#7"
    final_path = download_dir / f"{video_id}#7.mp3"
    # TODO: dont put video id as 7; either receive a video id or don't download.

    # TODO: Implement a proper orchestrator singleton to handle status updates and database persistence.
    # Do not implement DB updates or status tracking in this module for now. Write these as TODO comments instead.

    # Dispatch mapping for different sources
    download_fn_map = {
        VideoSource.YOUTUBE: download_youtube,
    }

    download_fn = download_fn_map[source]
    if not download_fn:
        diag.error(f"download_video: No download function found for source {source}")
        return None

    try:
        download_fn(video_id, tmp_download_path)
        return final_path
    except Exception as e:
        diag.error(f"download_video: Failed to download video {video_id} via {source}: {e}")
        return None

