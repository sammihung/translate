"""
QwenASR Pro - pywebview launcher
Opens a frameless window with React UI, starts FastAPI backend in background
"""

import sys
import os
import threading
import webview
from pathlib import Path

os.environ["TRANSFORMERS_VERBOSITY"] = "error"

src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.logging_config import setup_logging, get_logger
from config.settings import config
import logging

log_level_str = getattr(config, 'log_level', 'INFO')
log_level = getattr(logging, log_level_str.upper(), logging.INFO)
logger = setup_logging(log_dir="logs", log_level=log_level, console_output=True, file_output=True)


BACKEND_PORT = 8000
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"


def start_backend():
    import uvicorn
    from backend import app
    uvicorn.run(app, host="127.0.0.1", port=BACKEND_PORT, log_level="warning")


class Api:
    def __init__(self):
        self.backend_url = f"http://127.0.0.1:{BACKEND_PORT}"

    def get_backend_url(self):
        return self.backend_url


def main():
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    import time
    time.sleep(2)

    api_instance = Api()

    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        url = str(index_path)
    else:
        url = f"http://localhost:3000"
        logger.warning(f"Frontend dist not found at {FRONTEND_DIR}, falling back to dev server at {url}")

    window = webview.create_window(
        title="QwenASR Pro",
        url=url,
        js_api=api_instance,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(800, 600),
        frameless=False,
        easy_drag=True,
    )

    logger.info("Launching pywebview window...")
    webview.start(debug=False)
    logger.info("Application closed")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)