from pymongo import MongoClient

# Mongo Connection
client = MongoClient("mongodb://localhost:27017/")

# Database
db = client["insurance_db"]

# Collections
POLICY_COLLECTION = db["policies"]


def insert_data_json(data):
    """
    Insert policy metadata into policies collection
    """
    if isinstance(data, dict):
        result = POLICY_COLLECTION.insert_one(data)
        print("Policy Inserted ID:", result.inserted_id)

    elif isinstance(data, list):
        result = POLICY_COLLECTION.insert_many(data)
        print("Policies Inserted:", len(result.inserted_ids))

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


