import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from videos import VideoSource
from videos.storage import JobPaths


@dataclass
class Job:
    """Unit of work that flows through every pipeline stage, accumulating artifacts."""
    id: int
    video_id: str
    source: VideoSource
    paths: JobPaths

    # Artifacts, populated by the stage that produces them
    audio_path: Optional[Path] = None
    srt_path: Optional[Path] = None

    # Reserved for future cancellation support; checked between stages
    cancelled: threading.Event = field(default_factory=threading.Event)

    @classmethod
    def create(cls, id: int, video_id: str, source: VideoSource) -> "Job":
        source = VideoSource(source)
        return cls(
            id=id,
            video_id=video_id,
            source=source,
            paths=JobPaths.for_job(source, video_id, id),
        )

    def __str__(self) -> str:
        return f"{self.source.value}::{self.video_id} (ID: {self.id})"
