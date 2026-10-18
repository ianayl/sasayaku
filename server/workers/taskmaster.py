from queue import Queue
from threading import Thread, Lock
from typing import Type, Any

import utils
from .tasks import DownloadTask, TranscriptionTask
from .download_worker import DownloadWorker
from .transcribe_worker import TranscribeWorker

diag = utils.gen_diag("Taskmaster")

class Taskmaster:
    def __init__(self, download_queue_maxsize: int = 0, transcription_queue_maxsize: int = 0):
        # TODO decide if I want to keep this maxsize
        # Bounded queues prevent unconstrained memory usage if workers fall behind
        self.download_queue = Queue(maxsize=download_queue_maxsize)
        self.transcription_queue = Queue(maxsize=transcription_queue_maxsize)
        
        self.workers = []
        # Lock used to futureproof dynamic worker scaling + prevent data inconsistencies during shutdown
        self._workers_lock = Lock()
        self.is_running = True

    def submit_download_task(self, db_id: int, video_id: str, video_source: Any) -> None:
        task = DownloadTask(
            id=db_id,
            video_id=video_id,
            video_source=video_source
        )
        self.download_queue.put(task)
        diag.info(f"Submitted DownloadTask for video {video_id} (ID: {db_id})")

    def submit_transcription_task(self, db_id: int, video_id: str, audio_path: str, output_srt_path: str) -> None:
        task = TranscriptionTask(
            id=db_id,
            video_id=video_id,
            audio_path=audio_path,
            output_srt_path=output_srt_path
        )
        self.transcription_queue.put(task)
        diag.info(f"Submitted TranscriptionTask for video {video_id} (ID: {db_id})")

    def start_workers(
        self, 
        download_worker = DownloadWorker, 
        transcribe_worker = TranscribeWorker, 
        download_count: int = 1, 
        transcribe_count: int = 1
    ) -> None:
        """Initializes and starts background download and transcription workers."""
        with self._workers_lock:
            # Initialize Download Workers
            for i in range(download_count):
                worker = download_worker(self, worker_id=i + 1)
                worker.start()
                self.workers.append(worker)

            # Initialize Transcription Workers
            for i in range(transcribe_count):
                worker = transcribe_worker(self, worker_id=i + 1)
                worker.start()
                self.workers.append(worker)

        diag.info(f"Started {download_count} download workers and {transcribe_count} transcription workers")

    def shutdown(self, timeout: float = 5.0) -> None:
        """Signals all workers to stop and waits for them to exit cleanly."""
        self.is_running = False

        with self._workers_lock:
            workers_to_join = list(self.workers)

        # Signal stop flag to all active workers
        for worker in workers_to_join:
            worker.stop()

        # Wait for threads to finish executing current tasks (with timeout protection)
        for worker in workers_to_join:
            worker.join(timeout=timeout)
            if worker.is_alive():
                diag.warning(f"Worker {worker.name} did not shut down gracefully within the timeout period.")

        diag.info("Taskmaster shut down completely")

# Global instance
taskmaster = Taskmaster()
