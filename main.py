import logging
from src.settings.config import setup_logging

def main():
    logger = logging.getLogger(__name__)
    setup_logging()



if __name__ == "__main__":
    main()
