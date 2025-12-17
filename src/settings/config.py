import logging
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DATA = Path(BASE_DIR) / "data" / "raw"
PROCESSED_DATA = Path(BASE_DIR) / 'data' / 'processed'
ARCHIVE_DATA = Path(BASE_DIR) / 'data' / 'archive'
FINAL_DATA = Path(BASE_DIR) / 'data' / 'final'

FOLDERS = [RAW_DATA, PROCESSED_DATA, ARCHIVE_DATA, FINAL_DATA]

LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'app.log'
LOG_LEVEL = logging.INFO

def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger()

    if not logger.hasHandlers():
        fileHandler = logging.FileHandler(LOG_FILE)
        streamHandler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s')
        fileHandler.setFormatter(formatter)
        streamHandler.setFormatter(formatter)

        logger.setLevel(LOG_LEVEL)
        logger.addHandler(fileHandler)
        logger.addHandler(streamHandler)
        