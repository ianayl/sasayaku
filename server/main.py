import logging

import videos
from backend import create_backend
from utils.config import CONFIG
from workers.taskmaster import taskmaster

logging.basicConfig(filename=CONFIG("logging.file_path"), level=logging.INFO)
backend = create_backend()

if __name__ == '__main__':
    videos.init_db()
    # Start workers
    # TODO: we don't actually have concurrency guards to support multiple
    # downloads and transcribes; Taskmaster defaults to 1 worker per stage.
    taskmaster.start_workers()

    backend.run(port=7749, debug=True, use_reloader=False)
