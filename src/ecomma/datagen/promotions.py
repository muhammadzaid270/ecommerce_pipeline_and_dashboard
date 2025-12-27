import random
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker

logger = logging.getLogger(__name__)
fake = Faker()

def generate_promotions_data(RAW_DATA_DIR, num_rows=15000):
    logger.info(f"Generating {num_rows} rows of promotions data...")
    
    data = []
    
    promo_types = ['percentage_off', 'fixed_amount', 'bogo', 'free_shipping', 'bundle_deal']
    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Beauty', 'Sports', 'Books', 'Toys']
    status_opts = ['active', 'expired', 'scheduled', 'paused']
    
    prefixes = ['SAVE', 'GET', 'FLASH', 'DEAL', 'HOT', 'NEW', 'VIP', 'BULK']
    suffixes = ['2024', '50', 'NOW', 'SALE', '25', '100']
    
    for _ in range(num_rows):
        promo_id = f"PR-{random.randint(1000, 99999)}"
        if random.random() < 0.08:
            promo_id = f"promo_{random.randint(100, 9999)}"
        
        promo_type = random.choice(promo_types)
        
        if random.random() < 0.15:
            code = None
        else:
            code_parts = [random.choice(prefixes)]
            if random.random() > 0.3:
                code_parts.append(random.choice(suffixes))
            code = ''.join(code_parts)
            
            if random.random() < 0.25:
                code = code.lower()
            elif random.random() < 0.10:
                code = f" {code}"
        
        if promo_type == 'percentage_off':
            discount_val = random.choice([5, 10, 15, 20, 25, 30, 40, 50, 60, 75])
        elif promo_type == 'fixed_amount':
            discount_val = random.choice([5, 10, 15, 20, 25, 50, 100])
        elif promo_type == 'bogo':
            discount_val = random.choice([50, 100])
        else:
            discount_val = None
        
        roll_disc = random.random()
        if discount_val is None or roll_disc < 0.12:
            discount = None
        elif roll_disc < 0.35:
            discount = f"{discount_val}%"
        elif roll_disc < 0.55 and promo_type == 'fixed_amount':
            discount = f"${discount_val}"
        else:
            discount = discount_val
        
        start_dt = fake.date_between(start_date='-200d', end_date='now')
        duration = random.randint(3, 45)
        end_dt = start_dt + timedelta(days=duration)
        
        fmt_roll = random.random()
        if fmt_roll < 0.30:
            start_date = start_dt.strftime("%Y-%m-%d")
            end_date = end_dt.strftime("%Y-%m-%d")
        elif fmt_roll < 0.60:
            start_date = start_dt.strftime("%m/%d/%Y")
            end_date = end_dt.strftime("%m/%d/%Y")
        else:
            start_date = start_dt.strftime("%d-%b-%Y")
            end_date = end_dt.strftime("%d-%b-%Y")
        
        min_purchase = None
        if random.random() > 0.45:
            min_val = random.choice([25, 50, 75, 100, 150, 200])
            mp_roll = random.random()
            if mp_roll < 0.35:
                min_purchase = f"${min_val}"
            elif mp_roll < 0.65:
                min_purchase = min_val
            else:
                min_purchase = f"{min_val} USD"
        
        usage_lim = None
        if random.random() > 0.40:
            usage_lim = random.choice([1, 5, 10, 25, 50, 100, 500, 1000, None])
        
        used_ct = 0
        if usage_lim and random.random() > 0.25:
            used_ct = random.randint(0, int(usage_lim * random.uniform(0.5, 1.2)))
        
        category = random.choice(categories)
        if random.random() < 0.15:
            category = f" {category.lower()} "
        
        status = random.choice(status_opts)
        if random.random() < 0.18:
            status = status.upper()
        elif random.random() < 0.12:
            status_map = {'active': 'Active', 'expired': 'Expire', 'scheduled': 'Scheduled'}
            status = status_map.get(status, status)
        
        row = {
            "Promo_ID": promo_id,
            "Promo_Code": code,
            "Promo_Type": promo_type,
            "Discount_Value": discount,
            "Category": category,
            "Start_Date": start_date,
            "End_Date": end_date,
            "Min_Purchase": min_purchase,
            "Usage_Limit": usage_lim,
            "Times_Used": used_ct,
            "Status": status
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    for col in df.columns:
        df.loc[df.sample(frac=0.025).index, col] = np.nan

    save_dir = RAW_DATA_DIR / 'marketing'
    save_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"promotions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    file_path = save_dir / filename
    
    logger.info(f"Saving DataFrame to {file_path}...")
    
    try:
        df.to_csv(file_path, index=False)
        logger.info("Promotions data generation complete.")
    except Exception as e:
        logger.error(f"Failed to save CSV file: {e}")

if __name__ == "__main__":
    from ecomma.settings.config import RAW_DATA as RAW_DATA_DIR, setup_logging
    setup_logging()
    generate_promotions_data(RAW_DATA_DIR, num_rows=30000)