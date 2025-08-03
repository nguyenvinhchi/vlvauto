# log_util.py

import logging
import io
import sys
from logging.handlers import RotatingFileHandler
import os

def create_logger(name="auto-tool", log_file="log/auto-tool.log", level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:  # Prevent duplicate handlers
        return logger

    # Wrap sys.stdout for UTF-8 encoding
    try:
        stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    except Exception:
        stream = sys.stdout

    stream_handler = logging.StreamHandler(stream)
    stream_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        mode='a',
        maxBytes=128 * 1024,
        backupCount=1,
        encoding='utf-8',
        delay=False
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
