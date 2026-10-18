import pathlib
import queue
import threading

import utils
import videos
from utils.config import CONFIG
from .tasks import DownloadTask

class DownloadWorker(threading.Thread):
    def __init__(self, taskmaster, worker_id: int = 1):
        super().__init__(name=f"DownloadWorker-{worker_id}")
        self.diag = utils.gen_diag(f"DownloadWorker[{worker_id}]")
        self.daemon = True
        self._stop_event = threading.Event()
        self._taskmaster = taskmaster
        self._worker_id = worker_id

    def stop(self):
        self._stop_event.set()

    def run(self):
        self.diag.info(f"DownloadWorker {self._worker_id} started")
        while not self._stop_event.is_set() and self._taskmaster.is_running:
            try:
                # Wait for a task with a timeout so stop flags can be checked
                task: DownloadTask = self._taskmaster.download_queue.get(timeout=1.0)
            except queue.Empty:
                continue  # Safe idle loop
            except Exception as e:
                self.diag.error(f"Error reading from download queue: {e}")
                continue

            # Ensure task_done() is always called, even if processing fails
            try:
                self._process_task(task)
            except Exception as e:
                self.diag.error(f"Error processing task for video {getattr(task, 'video_id', 'unknown')}: {e}")
            finally:
                self._taskmaster.download_queue.task_done()

        self.diag.info(f"DownloadWorker {self._worker_id} stopped")

    def _process_task(self, task: DownloadTask) -> None:
        video_id = task.video_id
        video_source = task.video_source
        db_id = task.id

        self.diag.info(f"Processing download for video {video_id} (ID: {db_id})")

        try:
            final_path = videos.download_video(video_id, video_source)

            if not final_path:
                raise RuntimeError(f"Downloader returned empty path for video {video_id}")

            self.diag.info(f"Successfully downloaded {video_id} to {final_path}")
            videos.update_status(db_id, videos.VideoStatus.PENDING_PROCESSING)

            # Construct paths
            base_path = pathlib.Path(CONFIG("downloads.downloads_path"))
            download_dir = base_path / video_source.value / video_id
            download_dir.mkdir(parents=True, exist_ok=True)
            final_srt_path = download_dir / f"{video_id}#7.srt"

            # Submit transcription task back to taskmaster
            self._taskmaster.submit_transcription_task(
                db_id=db_id,
                video_id=video_id,
                audio_path=str(final_path),
                output_srt_path=str(final_srt_path)
            )

        except Exception as e:
            self.diag.error(f"Failed to process download task for video {video_id}: {e}")
            # Ensure the database reflects the failure instead of leaving it hanging
            videos.update_status(db_id, videos.VideoStatus.DOWNLOAD_FAILED)

