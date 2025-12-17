import requests
import logging
import json
import time
from datetime import datetime

logger = logging.getLogger(__name__)

def fetch_data(base_url, resource):
    all_items = []
    skip = 0
    limit = 30

    while True:
        url = f"{base_url}/{resource}?limit={limit}&skip={skip}"

        try:
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                items = data.get(resource, [])
                if not items:
                    break
                all_items.extend(items)
                skip += limit
                logger.info(f"Fetched {len(items)} items, total so far: {len(all_items)}")
                time.sleep(0.5)
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                break
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            break
    return all_items


def save_raw_json(file_path, data, resource):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{resource}_{timestamp}.json"
    file_path = file_path / filename
    
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        logger.info(f"SUCCESS: Saved raw data to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save JSON: {e}")