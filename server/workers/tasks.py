from dataclasses import dataclass

@dataclass
class DownloadTask:
    id: int
    video_id: str
    video_source: str

@dataclass
class TranscriptionTask:
    id: int
    video_id: str
    audio_path: str
    output_srt_path: str
