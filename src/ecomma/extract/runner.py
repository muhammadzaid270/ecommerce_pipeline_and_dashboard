import logging
from ecomma.settings.config import RAW_DATA
from ecomma.extract.extraction import fetch_data, save_raw_json

logger = logging.getLogger(__name__)

def run_extraction():
    '''This function will run the extraction process for products, users, and carts from the dummyjson.com API. It will fetch the data using the fetch_data function and save it using the save_raw_json function.'''

    base_url = "https://dummyjson.com"

    products_file_path = RAW_DATA / 'products'
    users_file_path = RAW_DATA / 'users'
    carts_file_path = RAW_DATA / 'carts'

    file_paths = [products_file_path, users_file_path, carts_file_path]
    for file_path in file_paths:
        file_path.mkdir(parents=True, exist_ok=True)

    # Call the functions and save the data
    products = fetch_data(base_url, "products")
    if products:
        save_raw_json(products_file_path, products, "products")
    
    users = fetch_data(base_url, "users")
    if users:
        save_raw_json(users_file_path, users, "users")
    
    carts = fetch_data(base_url, "carts")
    if carts:
        save_raw_json(carts_file_path, carts, "carts")

    logger.debug(f"Extraction run completed. Products: {len(products)}, Users: {len(users)}, Carts: {len(carts)}. Data saved to {RAW_DATA}")

if __name__ == "__main__":
    run_extraction()
