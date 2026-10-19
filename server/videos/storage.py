from dataclasses import dataclass
from pathlib import Path

from utils.config import CONFIG
from .video import VideoSource


def downloads_root() -> Path:
    return Path(CONFIG("downloads.downloads_path"))


def video_dir(source: VideoSource, video_id: str) -> Path:
    return downloads_root() / VideoSource(source).value / video_id


@dataclass(frozen=True)
class JobPaths:
    """
    Single source of truth for on-disk layout:
        <downloads_root>/<source>/<video_id>/<video_id>.mp3 (shared across jobs)
        <downloads_root>/<source>/<video_id>/<video_id>#<job_id>.srt (per job)
        <downloads_root>/<source>/<video_id>/thumbnail.<ext> (latest thumbnail)
    """
    video_dir: Path
    audio_stem: Path
    srt: Path
    thumbnail_stem: Path

    @classmethod
    def for_job(cls, source: VideoSource, video_id: str, job_id: int) -> "JobPaths":
        video_dir_path = video_dir(source, video_id)
        return cls(
            video_dir=video_dir_path,
            # Extensionless: the downloader's postprocessor decides the final extension.
            audio_stem=video_dir_path / video_id,
            srt=video_dir_path / f"{video_id}#{job_id}.srt",
            thumbnail_stem=video_dir_path / "thumbnail",
        )

    def ensure_dirs(self) -> None:
        self.video_dir.mkdir(parents=True, exist_ok=True)
