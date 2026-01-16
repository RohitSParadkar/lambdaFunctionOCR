from pymongo import MongoClient
from datetime import datetime, timezone

client = MongoClient("mongodb://localhost:27017/")
db = client["insurance_db"]

FINAL_LOGS = db["policy_final_logs"]


def upsert_final_log(
    pdf_name: str,
    file_path: str,
    channel: str,
    rawdata: dict = None,
    status: str = "FAILED",
    failure_reason: str = None
):
    """
    One PDF = One document
    """
    FINAL_LOGS.update_one(
        {"pdf_name": pdf_name},
        {
            "$set": {
                "pdf_name": pdf_name,
                "file_path": file_path,
                "channel": channel,
                "rawdata_extracted": rawdata,
                "status": status,
                "failure_reason": failure_reason,
                "processed_at": datetime.now(timezone.utc).astimezone().isoformat()
            }
        },
        upsert=True
    )
