import logging
from ecomma.datagen import campaign_spend, promotions, orders
from ecomma.settings.config import RAW_DATA, setup_logging

logger = logging.getLogger(__name__)
setup_logging()
def run_data_generation():
    logger.info("Starting data generation process...")
    
    logger.info("Generating promotional data...")
    promotions.generate_promotions_data(RAW_DATA, 30000)
    
    logger.info("Generating campaign spend data...")
    campaign_spend.generate_marketing_data(RAW_DATA, 30000)
    
    logger.info("Generating orders data...")
    orders.generate_orders(RAW_DATA, 10000)
    
    logger.info("Data generation process completed.")

if __name__ == "__main__":
    run_data_generation()
