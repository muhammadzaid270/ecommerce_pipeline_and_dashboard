import random
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker

logger = logging.getLogger(__name__)
fake = Faker()

def generate_promo_id():
    if random.random() < 0.08:
        return f"promo_{random.randint(100, 9999)}"
    return f"PR-{random.randint(1000, 99999)}"

def generate_promo_code(prefixes, suffixes):
    if random.random() < 0.15:
        return None
    
    code_parts = [random.choice(prefixes)]
    if random.random() > 0.3:
        code_parts.append(random.choice(suffixes))
    code = ''.join(code_parts)
    
    if random.random() < 0.25:
        code = code.lower()
    elif random.random() < 0.10:
        code = f" {code}"
    
    return code

def get_discount_value(promo_type):
    if promo_type == 'percentage_off':
        return random.choice([5, 10, 15, 20, 25, 30, 40, 50, 60, 75])
    elif promo_type == 'fixed_amount':
        return random.choice([5, 10, 15, 20, 25, 50, 100])
    elif promo_type == 'bogo':
        return random.choice([50, 100])
    return None

def format_discount_value(discount_val, promo_type):
    roll_disc = random.random()
    
    if discount_val is None or roll_disc < 0.12:
        return None
    elif roll_disc < 0.35:
        return f"{discount_val}%"
    elif roll_disc < 0.55 and promo_type == 'fixed_amount':
        return f"${discount_val}"
    return discount_val

def format_promo_dates(start_dt, duration):
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
    
    return start_date, end_date

def get_min_purchase():
    if random.random() > 0.45:
        min_val = random.choice([25, 50, 75, 100, 150, 200])
        mp_roll = random.random()
        
        if mp_roll < 0.35:
            return f"${min_val}"
        elif mp_roll < 0.65:
            return min_val
        return f"{min_val} USD"
    return None

def get_usage_stats():
    usage_lim = None
    if random.random() > 0.40:
        usage_lim = random.choice([1, 5, 10, 25, 50, 100, 500, 1000, None])
    
    used_ct = 0
    if usage_lim and random.random() > 0.25:
        used_ct = random.randint(0, int(usage_lim * random.uniform(0.5, 1.2)))
    
    return usage_lim, used_ct

def apply_category_messiness(category):
    if random.random() < 0.15:
        return f" {category.lower()} "
    return category

def apply_status_messiness(status):
    if random.random() < 0.18:
        return status.upper()
    elif random.random() < 0.12:
        status_map = {'active': 'Active', 'expired': 'Expire', 'scheduled': 'Scheduled'}
        return status_map.get(status, status)
    return status

def generate_promotions_data(RAW_DATA_DIR, num_rows=15000):
    logger.info(f"Generating {num_rows} rows of promotions data...")
    
    data = []
    
    promo_types = ['percentage_off', 'fixed_amount', 'bogo', 'free_shipping', 'bundle_deal']
    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Beauty', 'Sports', 'Books', 'Toys']
    status_opts = ['active', 'expired', 'scheduled', 'paused']
    
    prefixes = ['SAVE', 'GET', 'FLASH', 'DEAL', 'HOT', 'NEW', 'VIP', 'BULK']
    suffixes = ['2024', '50', 'NOW', 'SALE', '25', '100']
    
    for _ in range(num_rows):
        promo_id = generate_promo_id()
        promo_type = random.choice(promo_types)
        code = generate_promo_code(prefixes, suffixes)
        
        discount_val = get_discount_value(promo_type)
        discount = format_discount_value(discount_val, promo_type)
        
        start_dt = fake.date_between(start_date='-200d', end_date='now')
        duration = random.randint(3, 45)
        start_date, end_date = format_promo_dates(start_dt, duration)
        
        min_purchase = get_min_purchase()
        usage_lim, used_ct = get_usage_stats()
        
        category = apply_category_messiness(random.choice(categories))
        status = apply_status_messiness(random.choice(status_opts))
        
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

    save_dir = RAW_DATA_DIR / 'promotions'
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