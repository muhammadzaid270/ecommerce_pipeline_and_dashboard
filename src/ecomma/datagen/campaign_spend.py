import random
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker

logger = logging.getLogger(__name__)
fake = Faker()

def generate_marketing_data(RAW_DATA_DIR, num_rows=15000):
    logger.info(f"Generating {num_rows} rows of marketing data...")
    
    data = []
    
    channels = ['Google Ads', 'Facebook', 'Instagram', 'TikTok', 'Email', 'Influencer']
    regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America']
    campaign_types = ['Summer_Sale', 'Black_Friday', 'New_User_Promo', 'Retargeting', 'Brand_Awareness']
    
    promo_pool = ['SAVE25', 'GET50', 'FLASH100', 'DEAL20', 'NEW100', 'VIP', 
                  'HOTSALE', 'BULK50', 'SAVENOW', 'FLASHNOW', 'GET100']
    
    for _ in range(num_rows):
        cid_num = random.randint(100, 9999)
        if random.random() < 0.05:
            campaign_id = f"id-{cid_num}"
        else:
            campaign_id = f"CMP-{cid_num}"
        
        channel = random.choice(channels)
        
        if random.random() < 0.30: 
            typos = {'Google Ads': 'Goggle Ads', 'Facebook': 'FaceBook', 'Instagram': 'Insta', 'TikTok': 'Tik Tok'}
            channel = typos.get(channel, channel)
            
        if random.random() < 0.20:
            channel = channel.lower()
            
        if random.random() < 0.15:
            channel = f" {channel} "

        region = random.choice(regions)
        if random.random() < 0.40:
            abbrevs = {'North America': 'NA', 'Europe': 'EU', 'Asia Pacific': 'APAC', 'Latin America': 'Latam'}
            region = abbrevs.get(region, region)

        start_date_obj = fake.date_between(start_date='-1y', end_date='now')
        duration = random.randint(5, 30)
        end_date_obj = start_date_obj + timedelta(days=duration)
        
        roll = random.random()
        if roll < 0.33:
            start_date = start_date_obj.strftime("%b %d, %Y")
            end_date = end_date_obj.strftime("%b %d, %Y")
        elif roll < 0.66:
            start_date = start_date_obj.strftime("%d/%m/%Y")
            end_date = end_date_obj.strftime("%d/%m/%Y")
        else:
            start_date = start_date_obj.strftime("%Y-%m-%d")
            end_date = end_date_obj.strftime("%Y-%m-%d")

        raw_spend = round(random.uniform(500.0, 50000.0), 2)
        roll_money = random.random()
        
        if roll_money < 0.10:
            spend = None
        elif roll_money < 0.40:
            spend = f"${raw_spend}"
        elif roll_money < 0.60:
            spend = f"{raw_spend} USD"
        else:
            spend = raw_spend

        if spend is None or isinstance(spend, str):
            base_spend = raw_spend
        else:
            base_spend = spend
            
        impressions = int(base_spend * random.uniform(50, 150))
        clicks = int(impressions * random.uniform(0.01, 0.05))
        
        promo_linked = None
        if random.random() < 0.65:
            promo_linked = random.choice(promo_pool)
            
            if random.random() < 0.18:
                promo_linked = promo_linked.lower()
            elif random.random() < 0.08:
                promo_linked = f" {promo_linked} "

        row = {
            "Campaign_ID": campaign_id,
            "Channel": channel,
            "Target_Region": region,
            "Start_Date": start_date,
            "End_Date": end_date,
            "Budget_Spend": spend,
            "Impressions": impressions,
            "Clicks": clicks,
            "Campaign_Type": random.choice(campaign_types),
            "Promo_Code_Linked": promo_linked if promo_linked else ""
        }
        data.append(row)

    df = pd.DataFrame(data)
    
    for col in df.columns:
        df.loc[df.sample(frac=0.02).index, col] = np.nan

    save_dir = RAW_DATA_DIR / 'marketing'
    save_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"marketing_spend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    file_path = save_dir / filename
    
    logger.info(f"Saving DataFrame to {file_path}...")
    
    try:
        df.to_csv(file_path, index=False)
        logger.info("Marketing data generation complete.")
    except Exception as e:
        logger.error(f"Failed to save CSV file: {e}")

if __name__ == "__main__":
    from ecomma.settings.config import RAW_DATA as RAW_DATA_DIR, setup_logging
    setup_logging()
    generate_marketing_data(RAW_DATA_DIR, num_rows=30000)