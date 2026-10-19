from videos import VideoStatus, whisper
from .job import Job
from .stage_worker import StageWorker


class TranscribeWorker(StageWorker):
    stage_name = "transcribe"
    running_status = VideoStatus.PROCESSING
    done_status = VideoStatus.FINISHED
    failed_status = VideoStatus.PROCESSING_FAILED

    def setup(self) -> None:
        # Loaded lazily on first job so idle servers don't hold GPU memory
        self._model = None

    def handle(self, job: Job) -> None:
        if job.audio_path is None:
            raise RuntimeError(f"No audio artifact for {job}")

        if self._model is None:
            self._model = whisper.load_model()

        whisper.generate_subtitles(job.audio_path, job.paths.srt, model=self._model)
        job.srt_path = job.paths.srt