import queue
import threading
from abc import ABC, abstractmethod
from typing import ClassVar, Optional

import utils
import videos
from videos import VideoStatus
from .job import Job


class StageWorker(threading.Thread, ABC):
    """
    Generic pipeline stage: pulls Jobs from `in_queue`, runs `handle`, updates
    status, and puts the job into `out_queue` (the next stage's input queue,
    wired by the Taskmaster; None if this is the last stage). Subclasses only
    implement the stage-specific work.
    """
    stage_name: ClassVar[str]
    # Status set when a worker picks up a job (None = leave unchanged)
    running_status: ClassVar[Optional[VideoStatus]] = None
    # Status set after `handle` succeeds, before the job is passed on
    done_status: ClassVar[VideoStatus]
    failed_status: ClassVar[VideoStatus]

    def __init__(self, in_queue: "queue.Queue[Job]",
                 out_queue: Optional["queue.Queue[Job]"], worker_id: int = 1):
        name = f"{type(self).__name__}[{worker_id}]"
        super().__init__(name=name, daemon=True)
        self.diag = utils.gen_diag(name)
        self._in_queue = in_queue
        self._out_queue = out_queue
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def setup(self) -> None:
        """Hook run once on the worker thread before processing jobs."""

    @abstractmethod
    def handle(self, job: Job) -> None:
        """Performs the stage's work, recording produced artifacts on `job`. Raises on failure."""

    def run(self) -> None:
        self.diag.info("started")
        self.setup()
        while not self._stop_event.is_set():
            try:
                # Timeout so the stop flag is re-checked periodically
                job = self._in_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                self._process(job)
            except Exception as e:
                self.diag.error(f"Unhandled error processing {job}: {e}")
            finally:
                self._in_queue.task_done()

        self.diag.info("stopped")

    def _process(self, job: Job) -> None:
        if job.cancelled.is_set():
            self.diag.info(f"Skipping cancelled job {job}")
            return

        self.diag.info(f"Processing {job}")
        if self.running_status is not None:
            videos.update_status(job.id, self.running_status)

        try:
            self.handle(job)
        except Exception as e:
            self.diag.error(f"{self.stage_name} failed for {job}: {e}")
            videos.update_status(job.id, self.failed_status)
            return

        self.diag.info(f"{self.stage_name} finished for {job}")
        # Set status before passing on so the next stage's status can't be overwritten
        videos.update_status(job.id, self.done_status)

        if self._out_queue is None:
            self.diag.info(f"Pipeline complete for {job}")
        else:
            self._out_queue.put(job)
