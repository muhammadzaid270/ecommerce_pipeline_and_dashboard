import logging
from ecomma.settings.config import setup_logging
from ecomma.extract.runner import run_extraction

def main():
    logger = logging.getLogger(__name__)
    setup_logging()

    logger.info("Starting the extraction process.")

    run_extraction()

if __name__ == "__main__":
    main()
