from dataclasses import dataclass
from pathlib import Path

from utils.config import CONFIG
from .video import VideoSource


def downloads_root() -> Path:
    return Path(CONFIG("downloads.downloads_path"))


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
    def video_dir_for(cls, source: VideoSource, video_id: str) -> Path:
        return downloads_root() / VideoSource(source).value / video_id

    @classmethod
    def thumbnail_path_for(cls, source: VideoSource, video_id: str) -> Path | None:
        """
        Resolves the stored thumbnail file for a video, regardless of extension.
        Returns None when the thumbnail does not exist.
        """
        video_dir = cls.video_dir_for(source, video_id)
        if not video_dir.exists():
            return None

        candidates = list(video_dir.glob("thumbnail.*"))
        if not candidates:
            return None

        return max(candidates, key=lambda path: path.stat().st_mtime)

    @classmethod
    def for_job(cls, source: VideoSource, video_id: str, job_id: int) -> "JobPaths":
        video_dir = cls.video_dir_for(source, video_id)
        return cls(
            video_dir=video_dir,
            # Extensionless: the downloader's postprocessor decides the final extension.
            audio_stem=video_dir / video_id,
            srt=video_dir / f"{video_id}#{job_id}.srt",
            thumbnail_stem=video_dir / "thumbnail",
        )

    def ensure_dirs(self) -> None:
        self.video_dir.mkdir(parents=True, exist_ok=True)
