import queue
import threading

import utils
import videos
from videos import whisper
from .tasks import TranscriptionTask

class TranscribeWorker(threading.Thread):
    def __init__(self, taskmaster, worker_id: int = 1):
        super().__init__(name=f"TranscribeWorker-{worker_id}")
        self.daemon = True
        self.diag = utils.gen_diag(f"TranscribeWorker[{worker_id}]")
        self._stop_event = threading.Event()
        self._taskmaster = taskmaster
        self._worker_id = worker_id

    def stop(self) -> None:
        """Signals the worker thread to stop gracefully."""
        self._stop_event.set()

    def run(self) -> None:
        self.diag.info(f"TranscribeWorker {self._worker_id} started")
        while not self._stop_event.is_set() and self._taskmaster.is_running:
            try:
                # Wait for a task with a timeout so stop flags can be checked
                task: TranscriptionTask = self._taskmaster.transcription_queue.get(timeout=1.0)
            except queue.Empty:
                continue  # Safe idle loop when queue is empty
            except Exception as e:
                self.diag.error(f"Error reading from transcription queue: {e}")
                continue

            # Ensure task_done() is always called, even if processing fails
            try:
                self._process_task(task)
            except Exception as e:
                self.diag.error(f"Unexpected error processing transcription task for video {getattr(task, 'video_id', 'unknown')}: {e}")
            finally:
                self._taskmaster.transcription_queue.task_done()

        self.diag.info(f"TranscribeWorker {self._worker_id} stopped")

    def _process_task(self, task: TranscriptionTask) -> None:
        """Handles the complete lifecycle of a single transcription task."""
        video_id = task.video_id
        audio_path = task.audio_path
        output_srt_path = task.output_srt_path
        db_id = task.id

        self.diag.info(f"Processing transcription for video {video_id} (ID: {db_id})")

        try:
            # Use the existing whisper logic
            # NOTE: This currently reloads the model every time, but keeps safety intact.
            success = whisper.generate_subtitles(audio_path, output_srt_path)

            if success:
                self.diag.info(f"Successfully transcribed {video_id}")
                videos.update_status(db_id, videos.VideoStatus.FINISHED)
            else:
                self.diag.error(f"Failed to transcribe {video_id}")
                videos.update_status(db_id, videos.VideoStatus.PROCESSING_FAILED)

        except Exception as e:
            self.diag.error(f"Exception thrown during subtitle generation for video {video_id}: {e}")
            # Ensure database doesn't stay stuck in an intermediate state on hard crashes
            videos.update_status(db_id, videos.VideoStatus.PROCESSING_FAILED)
