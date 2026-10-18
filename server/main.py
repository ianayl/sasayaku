import logging

import videos 
from backend import create_backend
from utils.config import CONFIG

logging.basicConfig(filename=CONFIG("logging.file_path"), level=logging.INFO)

backend = create_backend()
if __name__ == '__main__':
    videos.init_db()
    backend.run(port=7749, debug=True, use_reloader=False)

