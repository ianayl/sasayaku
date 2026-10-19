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
        result = videos.download_audio(job.video_id, job.source, job.paths)
        job.audio_path = result.audio_path
        # Video metadata is stored in a separate database table, and linked via
        # the video ID primary key. Upsert automatically links metadata to the
        # video.
        videos.upsert_video_metadata(
            result.metadata.video_id,
            result.metadata.video_source,
            result.metadata.title,
            result.metadata.author,
            result.metadata.metadata_date,
        )
        self.diag.info(f"Downloaded {job} to {job.audio_path}")
