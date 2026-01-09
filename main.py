from img_xml_text_extractor import extract_text_from_pdf_via_svg_all_pages
from gemini_extractor import extract_insurance_metadata
import json
from api_call import (
    upload_document_to_dolphin_dms,
    download_document_from_dolphin_dms,
)
def filter_metadata(metadata: dict) -> dict:
    """
    Pick only required fields from extracted metadata
    """
    required_fields = [
  "Policy_Number",
  "Insured_Name",
  "Insured_Contact_No",
  "Insurance_Company_Name",
  "Previous_Insurance_Company",
  "Products",
  "Policy_Start_Date",
  "Policy_Expiry_Date",
  "Sum_Assured_OR_IDV",
  "Net_Premium",
  "Vehicle_Registration_No",
  "Business_Or_Retention_Type",
    ]

    return {
        key: metadata.get(key)
        for key in required_fields
        if key in metadata and metadata.get(key) not in ("", None)
    }

def get_additional_fields() -> dict:
    return {
        "Channel": "Worksite",
    }

def build_policy_payload(metadata: dict) -> dict:
    filtered_metadata = filter_metadata(metadata)
    additional_fields = get_additional_fields()

    combined_payload = {
        **filtered_metadata,
        **additional_fields
    }

    return combined_payload
def main():
    """
    Provide the file path from local system in below variable
    Example:
    PDF_PATH = "./data/10000*****.pdf (url from local data directory)
    """
    PDF_PATH = "./data/test_data/data/motorData/Go_Digital/DG_4W_SCHEDULESC_D169759143_1736159709682.pdf"

    result = extract_text_from_pdf_via_svg_all_pages(PDF_PATH)
    text = result["full_text"]

    print("Total number of characters in document:", len(text))

    metadata = extract_insurance_metadata(text)
    policy_data = build_policy_payload(metadata)
    print("Final Schema:",policy_data)

    print(json.dumps(metadata, ensure_ascii=False, indent=2))

    response = upload_document_to_dolphin_dms(
    file_path=PDF_PATH,
    policy_data=policy_data
    )
    # PRINT FULL SERVER RESPONSE
    print("Upload Response from Server:")
    print(response)

    #  OPTIONAL: PRINT ONLY MONGO ID
    if isinstance(response, dict) and "mongoId" in response:
        print("mongoId", response["mongoId"])




# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()
