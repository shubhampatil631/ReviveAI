import os
import csv
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from backend.app.db.mongo import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_mongo")

async def seed_mongo():
    await db_manager.connect()
    
    customers_col = db_manager.get_collection("customers")
    transactions_col = db_manager.get_collection("transactions")
    
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_transactions.csv")
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found at {csv_path}")
        return

    count_txns = await transactions_col.count_documents({})
    if count_txns > 0:
        logger.info(f"MongoDB already contains {count_txns} transactions. Skipping seed.")
        return

    logger.info(f"Seeding Mongo database from {csv_path}...")
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cust_id = row["customer_id"]
            cust_doc = {
                "customer_id": cust_id,
                "name": row["customer_name"],
                "email": row["customer_email"],
                "phone": row["customer_phone"],
                "payment_methods": [row["payment_method"]],
                "opt_out": row["opt_out"].lower() == "true",
                "history": {
                    "past_recoveries": 1 if row["opt_out"].lower() == "false" else 0,
                    "past_failures": 1,
                    "lifetime_value": float(row["amount"]) * 2
                }
            }
            existing_cust = await customers_col.find_one({"customer_id": cust_id})
            if not existing_cust:
                await customers_col.insert_one(cust_doc)

            txn_doc = {
                "transaction_id": row["transaction_id"],
                "customer_id": cust_id,
                "amount": float(row["amount"]),
                "currency": row["currency"],
                "event_type": row["event_type"],
                "status": "failed",
                "failure_reason": row["failure_reason"],
                "timestamp": datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            }
            await transactions_col.insert_one(txn_doc)

    logger.info("Successfully seeded MongoDB with initial synthetic transactions and customers.")

if __name__ == "__main__":
    asyncio.run(seed_mongo())
