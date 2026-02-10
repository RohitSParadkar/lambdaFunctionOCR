import os
import shutil
from datetime import datetime, timezone

from img_xml_text_extractor import extract_text_from_pdf_via_svg_all_pages
from extractor import save_full_text_to_file
from gemini_extractor import extract_insurance_metadata
from api_call import upload_document_to_dolphin_dms
from logger import upsert_final_log

# ==============================
# CONFIG
# ==============================
BASE_FOLDER_PATH = "./Folder_Structure"

PROCESS_FOLDERS = [
    "Automatic_Preprocess",
    "Manual_Preprocess"
]

PROCESSED_FOLDER = "Process_Files"
UNPROCESSED_FOLDER = "Unprocess_Files"

CHANNELS = [
    "D2C",
    "Digital POSP",
    "Embedded",
    "Institutional",
    "Worksite"
]

# ==============================
# FIELD DEFINITIONS
# ==============================
MANDATORY_FIELDS = [
    "Policy_Number",
    "Insured_Name",
    "Product_Subtype",
    "Insured_Contact_No",
    "Insurance_Company_Name",
    "Products",
    "Policy_Start_Date",
    "Policy_Expiry_Date",
    "Sum_Assured_OR_IDV",
    "Net_Premium",
    "Gross_or_Total_Premium",
    "Business_Or_Retention_Type",
]

OPTIONAL_FIELDS = [
    "Vehicle_Registration_No"
]

# ==============================
# METADATA VALIDATION
# ==============================
def validate_and_filter_metadata(metadata: dict):
    valid_data = {}
    missing = []

    for field in MANDATORY_FIELDS:
        value = metadata.get(field)
        if value in ("", None):
            missing.append(field)
        else:
            valid_data[field] = value

    for field in OPTIONAL_FIELDS:
        value = metadata.get(field)
        if value not in ("", None):
            valid_data[field] = value

    return valid_data, missing

# ==============================
# CHANNEL DETECTION
# ==============================
def detect_channel_from_path(file_path: str):
    path = file_path.replace("\\", "/").lower()
    for channel in CHANNELS:
        if channel.lower() in path:
            return channel
    return None

# ==============================
# MOVE FILE WITH STRUCTURE
# ==============================
def move_file_with_structure(src_path, target_root, base_folder, channel):
    rel_path = os.path.relpath(src_path, base_folder)
    parts = rel_path.split(os.sep)

    if channel and parts[0].lower() == channel.lower():
        parts = parts[1:]

    target_path = (
        os.path.join(target_root, channel, *parts)
        if channel else
        os.path.join(target_root, *parts)
    )

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    shutil.move(src_path, target_path)

    print(f"File moved → {target_path}")

# ==============================
# HEALTH PREMIUM NORMALIZATION
# ==============================
def normalize_health_premium_fields(metadata: dict) -> dict:
    """
    If Products == 'Health' and either Net_Premium or Gross_or_Total_Premium
    is missing, copy the available value to the missing field.
    """

    if metadata.get("Products") != "Health":
        return metadata

    net_premium = metadata.get("Net_Premium")
    gross_premium = metadata.get("Gross_or_Total_Premium")

    # If one is present and the other is missing, copy value
    if net_premium and not gross_premium:
        metadata["Gross_or_Total_Premium"] = net_premium

    elif gross_premium and not net_premium:
        metadata["Net_Premium"] = gross_premium

    return metadata

# ==============================
# LIABILITY ONLY IDV NORMALIZATION
# ==============================
def normalize_liability_only_idv(metadata: dict) -> dict:
    """
    If Product_Subtype contains 'liability only policy'
    (case-insensitive) and Sum_Assured_OR_IDV is missing,
    set it to 0.
    """

    product_subtype = metadata.get("Product_Subtype")
    sum_assured = metadata.get("Sum_Assured_OR_IDV")

    if (
        isinstance(product_subtype, str)
        and "liability only policy" in product_subtype.lower()
        and sum_assured in ("", None)
    ):
        metadata["Sum_Assured_OR_IDV"] = str(0)

    return metadata


# ==============================
# PROCESS SINGLE PDF
# ==============================
def process_single_pdf(pdf_path: str) -> dict:
    pdf_name = os.path.basename(pdf_path)
    channel = detect_channel_from_path(pdf_path)

    gemini_metadata = None  

    try:
        if os.path.getsize(pdf_path) == 0:
            raise ValueError("PDF file is empty")

        # PDF → TEXT
        pdf_data = extract_text_from_pdf_via_svg_all_pages(pdf_path)
        text = pdf_data.get("full_text", "")
        save_full_text_to_file(text)

        if not text.strip():
            raise ValueError("No text extracted from PDF")

        # TEXT → GEMINI
        gemini_metadata = extract_insurance_metadata(text)

        # HEALTH PREMIUM and liability FIX
        gemini_metadata = normalize_health_premium_fields(gemini_metadata)
        gemini_metadata = normalize_liability_only_idv(gemini_metadata)

        # VALIDATION
        valid_metadata, missing = validate_and_filter_metadata(gemini_metadata)

        if missing:
            raise ValueError(
                f"Missing mandatory fields: {', '.join(missing)}"
            )

        # DMS PAYLOAD
        payload = {**valid_metadata, "source_file": pdf_name}
        if channel:
            payload["Channel"] = channel

        dms_response = upload_document_to_dolphin_dms(
            file_path=pdf_path,
            policy_data=payload
        )

        if dms_response.get("status") != "SUCCESS":
            raise RuntimeError(
                dms_response.get("error", "DMS upload failed")
            )

        # SUCCESS LOG
        upsert_final_log(
            pdf_name=pdf_name,
            file_path=pdf_path,
            channel=channel,
            rawdata=gemini_metadata,
            status="SUCCESS",
            failure_reason=None
        )

        return {"status": "SUCCESS"}

    except Exception as e:
        # FAILURE LOG (ALWAYS EXECUTES)
        upsert_final_log(
            pdf_name=pdf_name,
            file_path=pdf_path,
            channel=channel,
            rawdata=gemini_metadata,   # ← present even when mandatory missing
            status="FAILED",
            failure_reason=str(e)
        )

        return {
            "status": "FAILED",
            "error": str(e)
        }


# ==============================
# POST PROCESSING
# ==============================
def handle_post_processing(pdf_path, result, top_level_folder):
    channel = result.get("channel")

    if result["status"] == "SUCCESS":
        target_root = os.path.join(BASE_FOLDER_PATH, PROCESSED_FOLDER)
    else:
        target_root = os.path.join(BASE_FOLDER_PATH, UNPROCESSED_FOLDER)

    move_file_with_structure(
        src_path=pdf_path,
        target_root=target_root,
        base_folder=top_level_folder,
        channel=channel
    )

# ==============================
# WALK & PROCESS
# ==============================
def process_selected_folders(base_path, folders):
    for folder in folders:
        top_level = os.path.join(base_path, folder)

        if not os.path.exists(top_level):
            continue

        for root, _, files in os.walk(top_level):
            for file in files:
                if file.lower().endswith(".pdf"):
                    pdf_path = os.path.join(root, file)
                    result = process_single_pdf(pdf_path)
                    handle_post_processing(pdf_path, result, top_level)

# ==============================
# MAIN
# ==============================
def main():
    print("Insurance PDF Processing Started")
    process_selected_folders(BASE_FOLDER_PATH, PROCESS_FOLDERS)
    print("Processing Completed")

if __name__ == "__main__":
    main()
