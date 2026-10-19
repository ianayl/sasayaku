from queue import Queue
from threading import Lock
from typing import Dict, List, Optional, Type

import utils
from videos import VideoSource
from .job import Job
from .stage_worker import StageWorker
from .download_worker import DownloadWorker
from .transcribe_worker import TranscribeWorker

diag = utils.gen_diag("Taskmaster")

# Ordered pipeline: each stage's output is routed into the next stage's queue.
DEFAULT_PIPELINE: List[Type[StageWorker]] = [DownloadWorker, TranscribeWorker]


class Taskmaster:
    def __init__(self, pipeline: List[Type[StageWorker]] = DEFAULT_PIPELINE,
                 queue_maxsize: int = 0):
        self.pipeline = list(pipeline)
        # TODO decide if I want to keep this maxsize
        # Bounded queues prevent unconstrained memory usage if workers fall behind
        self.queues: Dict[Type[StageWorker], "Queue[Job]"] = {
            stage: Queue(maxsize=queue_maxsize) for stage in self.pipeline
        }

        self.workers: List[StageWorker] = []
        # Lock used to futureproof dynamic worker scaling + prevent data inconsistencies during shutdown
        self._workers_lock = Lock()
        self.is_running = True

    def submit(self, db_id: int, video_id: str, source: VideoSource) -> Job:
        """Creates a Job and enqueues it at the first pipeline stage."""
        # TODO: check for duplicate in-flight jobs for the same video_id
        job = Job.create(id=db_id, video_id=video_id, source=source)
        self.queues[self.pipeline[0]].put(job)
        diag.info(f"Submitted {job}")
        return job

    def _next_queue(self, stage: Type[StageWorker]) -> Optional["Queue[Job]"]:
        """
        Returns the queue that `stage` should put finished jobs into, i.e. the
        input queue of the stage after it in the pipeline.

        Example, with pipeline = [DownloadWorker, TranscribeWorker]:
            _next_queue(DownloadWorker)   -> self.queues[TranscribeWorker]
            _next_queue(TranscribeWorker) -> None (last stage; job is done)
        """
        position = self.pipeline.index(stage)
        is_last_stage = position == len(self.pipeline) - 1
        if is_last_stage:
            return None

        next_stage = self.pipeline[position + 1]
        return self.queues[next_stage]

    def start_workers(self, counts: Optional[Dict[Type[StageWorker], int]] = None) -> None:
        """Starts `counts[stage]` workers (default 1) for every pipeline stage."""
        counts = counts or {}
        with self._workers_lock:
            for stage in self.pipeline:
                n = counts.get(stage, 1)
                for i in range(n):
                    worker = stage(
                        in_queue=self.queues[stage],        # The queue associated with the current stage
                        out_queue=self._next_queue(stage),  # The queue associated with the next stage
                        worker_id=i + 1,
                    )
                    worker.start()
                    self.workers.append(worker)
                diag.info(f"Started {n} {stage.stage_name} workers")

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
