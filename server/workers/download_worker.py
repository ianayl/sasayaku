import videos
from videos import VideoStatus
from .job import Job
from .stage_worker import StageWorker


class DownloadWorker(StageWorker):
    stage_name = "download"
    done_status = VideoStatus.PENDING_PROCESSING
    failed_status = VideoStatus.DOWNLOAD_FAILED

    def handle(self, job: Job) -> None:
        job.paths.ensure_dirs()
        job.audio_path = videos.download_audio(job.video_id, job.source, job.paths.audio_stem)
        self.diag.info(f"Downloaded {job} to {job.audio_path}")
