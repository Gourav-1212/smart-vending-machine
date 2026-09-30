"""Database seeding script for snacks, opening cash float, and backdated sales.


Uses settings from environment variables / .env:
- SEED_SNACK_COUNT (default 12)
- SEED_BACKDATED_DAYS (default 30)
- SEED_OPENING_FLOAT_MULTIPLIER (default 50)
"""


from datetime import datetime, timedelta, timezone
import logging
import random


from bson import ObjectId
from pymongo import MongoClient


from app.core.config import get_settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


CATALOG = [
    {"name": "Roasted Honey Almonds", "price": 50, "description": "Crunchy glazed almonds with organic honey"},
    {"name": "Dark Chocolate Sea Salt Bar", "price": 40, "description": "70% rich cocoa dark chocolate bar"},
    {"name": "Sea Salt Potato Crisps", "price": 25, "description": "Thin and crispy kettle cooked potato chips"},
    {"name": "Spicy Peri Peri Cashews", "price": 60, "description": "Slow roasted whole cashews with spicy peri peri"},
    {"name": "Oat & Berry Energy Bar", "price": 35, "description": "Wholesome rolled oats and dried cranberries"},
    {"name": "Baked Multigrain Nachos", "price": 30, "description": "Crispy baked corn and multigrain chips"},
    {"name": "Cheddar Cheese Pretzel Bites", "price": 45, "description": "Oven baked crunchy pretzel bites with cheddar"},
    {"name": "Sparkling Berry Water", "price": 20, "description": "Sugar-free sparkling water infused with berries"},
    {"name": "Caramel Glazed Popcorn", "price": 30, "description": "Freshly popped corn coated in brown sugar caramel"},
    {"name": "Matcha Green Tea Wafer", "price": 35, "description": "Crispy layered wafers filled with Japanese matcha cream"},
    {"name": "Hazelnut Chocolate Bites", "price": 50, "description": "Roasted hazelnuts covered in silky milk chocolate"},
    {"name": "Sour Cream & Chive Crackers", "price": 25, "description": "Lightly salted golden baked crackers"},
]




def seed_database():
    settings = get_settings()
    logger.info("Connecting to MongoDB at %s (DB: %s)", settings.mongo_uri, settings.mongo_db_name)
    client = MongoClient(settings.mongo_uri)
    db = client[settings.mongo_db_name]


    # 1. Seed Snacks
    snacks_to_create = CATALOG[: settings.seed_snack_count]
    snack_docs = []


    for item in snacks_to_create:
        existing = db["snacks"].find_one({"name": item["name"]})
        if not existing:
            doc = {
                "name": item["name"],
                "description": item["description"],
                "price": item["price"],
                "quantity": 15,
                "sold_out": False,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            res = db["snacks"].insert_one(doc)
            doc["_id"] = res.inserted_id
            snack_docs.append(doc)
            logger.info("Created snack: %s (ID: %s)", item["name"], res.inserted_id)
        else:
            snack_docs.append(existing)
            logger.info("Snack already exists: %s", item["name"])


    # 2. Seed Opening Cash Float (singleton in 'cash_float' collection)
    cash_float_doc = db["cash_float"].find_one({"_id": "singleton"})
    if not cash_float_doc:
        denominations_dict = {
            str(denom): settings.seed_opening_float_multiplier for denom in settings.denominations
        }
        db["cash_float"].insert_one({
            "_id": "singleton",
            "denominations": denominations_dict,
            "updated_at": datetime.now(timezone.utc),
        })
        logger.info("Seeded opening cash float into 'cash_float': %s", denominations_dict)
    else:
        logger.info("Cash float already exists in 'cash_float'. Skipping float seeding.")


    # 3. Seed Backdated Sales for Analytics
    existing_sales_count = db["sales"].count_documents({})
    if existing_sales_count < 10 and snack_docs:
        logger.info("Generating backdated sales for the past %d days...", settings.seed_backdated_days)
        now = datetime.now(timezone.utc)
        sales_records = []


        for day_offset in range(settings.seed_backdated_days, 0, -1):
            day_date = now - timedelta(days=day_offset)
            # 2 to 6 purchases per day
            transactions_count = random.randint(2, 6)


            for _ in range(transactions_count):
                chosen_snack = random.choice(snack_docs)
                qty = random.randint(1, 3)
                unit_price = chosen_snack["price"]
                total = unit_price * qty


                # Simulate customer cash received (either exact or rounded up to next 50/100)
                cash_candidates = [denom for denom in settings.denominations if denom >= total]
                cash_rec = min(cash_candidates) if cash_candidates else (total + 10)
                change = cash_rec - total


                random_hour = random.randint(8, 21)
                random_minute = random.randint(0, 59)
                sold_at = day_date.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)


                sales_records.append({
                    "snack_id": str(chosen_snack["_id"]),
                    "snack_name_at_sale": chosen_snack["name"],
                    "unit_price_at_sale": unit_price,
                    "quantity": qty,
                    "total_amount": total,
                    "cash_received": cash_rec,
                    "change_given": {str(change): 1} if change > 0 else {},
                    "sold_at": sold_at,
                })


        if sales_records:
            db["sales"].insert_many(sales_records)
            logger.info("Inserted %d backdated sale records successfully.", len(sales_records))
    else:
        logger.info("Sales collection already has %d records. Skipping backdated sales.", existing_sales_count)


    client.close()
    logger.info("Seeding completed successfully!")




if __name__ == "__main__":
    seed_database()