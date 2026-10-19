from dataclasses import dataclass
from datetime import datetime
from mimetypes import guess_extension
from pathlib import Path
from typing import Callable, Dict, Optional
from urllib.parse import urlparse
from urllib.request import urlopen

import yt_dlp

import utils
from .storage import JobPaths
from .video import VideoMetadata, VideoSource

diag = utils.gen_diag("download")


@dataclass(frozen=True)
class DownloadResult:
    audio_path: Path
    metadata: VideoMetadata
    thumbnail_path: Optional[Path] = None


def _choose_thumbnail_url(info: dict) -> Optional[str]:
    """
    Chooses the best available thumbnail URL from the video info dictionary.
    """
    thumbnail = info.get("thumbnail")
    if thumbnail:
        return thumbnail

    thumbnails = [entry for entry in info.get("thumbnails") or [] if entry.get("url")]
    if not thumbnails:
        return None

    best = max(
        thumbnails,
        key=lambda entry: (
            int(entry.get("height") or 0),
            int(entry.get("width") or 0),
        ),
    )
    return best["url"]


def _thumbnail_extension(thumbnail_url: str, content_type: Optional[str]) -> str:
    suffix = Path(urlparse(thumbnail_url).path).suffix.lstrip(".")
    if suffix:
        return suffix

    if content_type:
        guessed = guess_extension(content_type.split(";", 1)[0].strip())
        if guessed:
            return guessed.lstrip(".")

    return "jpg"


def _save_thumbnail(paths: JobPaths, thumbnail_url: Optional[str]) -> Optional[Path]:
    """
    Saves the thumbnail image for a video to the appropriate location on disk.
    """
    paths.ensure_dirs()
    for existing in paths.video_dir.glob("thumbnail.*"):
        existing.unlink(missing_ok=True)

    if not thumbnail_url:
        return None

    try:
        with urlopen(thumbnail_url, timeout=30) as response:
            content_type = response.headers.get_content_type()
            thumbnail_bytes = response.read()

        extension = _thumbnail_extension(thumbnail_url, content_type)
        thumbnail_path = paths.thumbnail_stem.with_suffix(f".{extension}")
        thumbnail_path.write_bytes(thumbnail_bytes)
        return thumbnail_path
    except Exception as e:
        diag.warning(
            f"_save_thumbnail: Failed to fetch thumbnail for {paths.video_dir.name}: {e}"
        )
        return None


def download_youtube(video_id: str, paths: JobPaths) -> DownloadResult:
    """
    Downloads audio and best-effort metadata from YouTube.
    """
    paths.ensure_dirs()
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
        'outtmpl': f"{paths.audio_stem}.%(ext)s",
        # Audio is shared per video_id and replaced on every request
        'overwrites': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_id, download=True)
    info = info or {}
    metadata_date = datetime.fromisoformat(utils.get_now_iso())
    # TODO: check for 403 and return error; also check for unknown errors
    # TODO: make sure this download doesn't hang.
    # TODO: add progress hooks
    # TODO: look into supporting bgutil_ytdlp_pot_provider

    downloads = (info or {}).get("requested_downloads") or []
    if not downloads or not downloads[0].get("filepath"):
        raise RuntimeError(f"yt-dlp did not report an output file for {video_id}")
    audio_path = Path(downloads[0]["filepath"])

    # Construct metadata for the downloaded video.
    metadata = VideoMetadata(
        video_id=video_id,
        video_source=VideoSource.YOUTUBE,
        title=info.get("title"),
        author=info.get("uploader") or info.get("channel") or info.get("creator"),
        metadata_date=metadata_date,
    )

    thumbnail_url = _choose_thumbnail_url(info)
    thumbnail_path = _save_thumbnail(paths, thumbnail_url)
    return DownloadResult(audio_path=audio_path, metadata=metadata, thumbnail_path=thumbnail_path)


_DOWNLOADERS: Dict[VideoSource, Callable[[str, JobPaths], DownloadResult]] = {
    VideoSource.YOUTUBE: download_youtube,
}


def download_audio(video_id: str, source: VideoSource, paths: JobPaths) -> DownloadResult:
    """
    Downloads audio for a video from the given source and returns its artifacts.
    """
    source = VideoSource(source)
    download_fn = _DOWNLOADERS.get(source)
    if download_fn is None:
        raise ValueError(f"No downloader registered for source {source.value}")

    diag.info(f"download_audio: Downloading {source.value}:{video_id} to {paths.audio_stem}.*")
    return download_fn(video_id, paths)
