import csv
import json
import random
import logging
from datetime import datetime, timedelta
from faker import Faker

logger = logging.getLogger(__name__)
fake = Faker()

def get_latest_file(RAW_DATA_DIR, folder_name):
    target_dir = RAW_DATA_DIR / folder_name
    if not target_dir.exists():
        return None
    files = sorted(target_dir.glob("*.jsonl"))
    return files[-1] if files else None

def load_seed_data(RAW_DATA_DIR):
    products_file = get_latest_file(RAW_DATA_DIR, "products")
    users_file = get_latest_file(RAW_DATA_DIR, "users")
    
    product_info = [] 
    user_ids = [1]

    if products_file:
        try:
            with open(products_file, 'r', encoding='utf-8') as f:
                items = [json.loads(line) for line in f if line.strip()]
                if items:
                    product_info = [{'id': p['id'], 'price': p.get('price', 0)} for p in items]
            logger.info(f"Loaded {len(product_info)} Products.")
        except Exception as e:
            logger.warning(f"Could not load products: {e}")

    if users_file:
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                items = [json.loads(line) for line in f if line.strip()]
                if items:
                    user_ids = [u['id'] for u in items]
            logger.info(f"Loaded {len(user_ids)} Users.")
        except Exception as e:
            logger.warning(f"Could not load users: {e}")
            
    if not product_info: 
        product_info = [{'id': 1, 'price': 10.0}]
    
    return product_info, user_ids

def generate_orders(RAW_DATA_DIR, num_orders=10000):
    product_info, user_ids = load_seed_data(RAW_DATA_DIR)
    logger.info(f"Generating {num_orders} orders...")
    
    promo_codes = ['SAVE25', 'GET50', 'FLASH100', 'DEAL20', 'NEW100', 'VIP', 
                   'HOTSALE', 'BULK50', 'SAVENOW', 'FLASHNOW', 'GET100']
    
    save_dir = RAW_DATA_DIR / 'orders'
    save_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"orders_{timestamp_str}.csv"
    file_path = save_dir / filename
    
    headers = [
        "order_id", 
        "user_id", 
        "order_date", 
        "status", 
        "total_amount",
        "subtotal_before_discount",
        "discount_applied",
        "promo_code_used",
        "product_cost",
        "payment_method", 
        "shipping_address", 
        "delivery_date"
    ]

    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for _ in range(num_orders):
                order_id = fake.unique.random_number(digits=8)
                user_id = random.choice(user_ids)
                
                order_date = fake.date_time_between(start_date='-1y', end_date='now')
                
                status_choices = ["COMPLETED", "PENDING", "SHIPPED", "CANCELLED", "RETURNED"]
                status = random.choice(status_choices)
                
                delivery_date = "" 
                
                if status in ["COMPLETED", "RETURNED"]:
                    days_to_ship = random.randint(2, 10)
                    d_date = order_date + timedelta(days=days_to_ship)
                    delivery_date = d_date.strftime("%Y-%m-%d")
                elif status == "SHIPPED":
                     days_est = random.randint(1, 5)
                     delivery_date = (order_date + timedelta(days=days_est)).strftime("%Y-%m-%d")
                
                num_items = random.randint(1, 5)
                cart_items = random.choices(product_info, k=num_items)
                
                subtotal = sum(item['price'] for item in cart_items)
                subtotal = round(subtotal, 2)
                
                avg_margin = random.uniform(0.35, 0.65)
                total_cost = round(subtotal * (1 - avg_margin), 2)
                
                promo_code = None
                discount_amt = 0
                
                if random.random() < 0.48:
                    promo_code = random.choice(promo_codes)
                    
                    if random.random() < 0.20:
                        promo_code = promo_code.lower()
                    elif random.random() < 0.10:
                        promo_code = f" {promo_code}"
                    
                    disc_pct = random.choice([0.05, 0.10, 0.15, 0.20, 0.25, 0.30])
                    discount_amt = round(subtotal * disc_pct, 2)
                    
                    if random.random() < 0.30:
                        discount_amt = round(discount_amt)
                
                total_amount = round(subtotal - discount_amt, 2)
                
                fmt_roll = random.random()
                if fmt_roll < 0.15:
                    if discount_amt > 0:
                        discount_applied = f"${discount_amt}"
                    else:
                        discount_applied = ""
                elif fmt_roll < 0.25:
                    if discount_amt > 0:
                        discount_applied = f"{discount_amt} USD"
                    else:
                        discount_applied = ""
                else:
                    discount_applied = discount_amt if discount_amt > 0 else ""
                
                subtotal_fmt = subtotal
                if random.random() < 0.12:
                    subtotal_fmt = f"${subtotal}"
                
                payment = random.choice(["Credit Card", "PayPal", "Debit Card", "Apple Pay"])
                address = fake.address().replace("\n", ", ")

                writer.writerow([
                    order_id,
                    user_id,
                    order_date.strftime("%Y-%m-%d %H:%M:%S"),
                    status,
                    total_amount,
                    subtotal_fmt,
                    discount_applied,
                    promo_code if promo_code else "",
                    total_cost,
                    payment,
                    address,
                    delivery_date
                ])
                
        logger.info(f"Successfully generated {num_orders} orders at {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to save orders: {e}")

if __name__ == "__main__":
    from ecomma.settings.config import RAW_DATA as RAW_DATA_DIR, setup_logging
    setup_logging()
    generate_orders(RAW_DATA_DIR, num_orders=15000)