import pandas as pd
from ecomma.settings.config import RAW_DATA, setup_logging
import logging

logger = logging.getLogger(__name__)
setup_logging()

def extract_from_sheets():
    SHEET_ID = "1nN0el0BiRtvPJs7QAuVMMAMU5VN8vDEgIAaJ2FuLdWg"
    GID = "0"

    csv_url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        f"/export?format=csv&gid={GID}"
    )

    try:
        df = pd.read_csv(csv_url)

        RAW_DATA.mkdir(parents=True, exist_ok=True)
        raw_file_path = RAW_DATA / "raw_orders.jsonl"

        df.to_json(raw_file_path, orient="records", lines=True)

        logger.info(f"Success! Extracted {len(df)} rows.")
        logger.info(f"Saved to: {raw_file_path}")

    except Exception as e:
        logger.error(f"Error extracting Google Sheet: {e}", exc_info=True)

if __name__ == "__main__":
    extract_from_sheets()