from api_call import (
    upload_document_to_dolphin_dms,
    download_document_from_dolphin_dms,
)

policy_data = {
  "channel": "Worksite",
  "policy_number": "35091132202500",
  "insured_name": "Rohit",
  "insured_contact_no": "33",
  "insurance_company_name": "Niva Bupa",
  "products": "4w",
  "policy_start_date": "02/02/2026",
  "policy_expiry_date": "02/02/2027",
  "sum_assured_or_idv": "44",
  "net_premium": "55",
  "vehicle_registration_no": "66",
  "business_or_retention_type": "Renewal"
}


# response = upload_document_to_dolphin_dms(
#     file_path="./data/test_data/data/NivaBupa/35091132202500.pdf",
#     policy_data=policy_data,
# )

# # PRINT FULL SERVER RESPONSE
# print("Upload Response from Server:")
# print(response)

# #  OPTIONAL: PRINT ONLY MONGO ID
# if isinstance(response, dict) and "mongoId" in response:
#     print("mongoId", response["mongoId"])


#=======================================download===============================
mongo_id = "695fb152940eb40503ae57a1"
response = download_document_from_dolphin_dms(
        mongo_id=mongo_id,
        save_path="downloads/policy.pdf",
    )

# PRINT FULL SERVER RESPONSE
print("Download Response from Server:")
print(response)