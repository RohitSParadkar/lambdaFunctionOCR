import json
from pymongo import MongoClient

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Database & Collection
db = client["insurance_db"]
collection = db["policies"]

def insert_json(data):
    """
    Insert dict or list of dicts into MongoDB
    """
    if isinstance(data, dict):
        result = collection.insert_one(data)
        print("Inserted ID:", result.inserted_id)

    elif isinstance(data, list):
        result = collection.insert_many(data)
        print("Inserted documents:", len(result.inserted_ids))

    else:
        raise ValueError("Data must be dict or list of dicts")


# Example JSON
json_data = {
    "policy_type": "Car",
    "policy_number": "CAR12345",
    "insured_name": "Rohit Paradkar",
    "vehicle_number": "MH12AB1234",
    "premium": 12500,
    "sum_insured": 500000
}


