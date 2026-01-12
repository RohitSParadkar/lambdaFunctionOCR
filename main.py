import os
import json
import shutil

from img_xml_text_extractor import extract_text_from_pdf_via_svg_all_pages
from gemini_extractor import extract_insurance_metadata
from api_call import upload_document_to_dolphin_dms

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
# METADATA FILTER
# ==============================
REQUIRED_FIELDS = [
    "Policy_Number",
    "Insured_Name",
    "Insured_Contact_No",
    "Insurance_Company_Name",
    "Products",
    "Policy_Start_Date",
    "Policy_Expiry_Date",
    "Sum_Assured_OR_IDV",
    "Net_Premium",
    "Gross_or_Total_Premium",
    "Vehicle_Registration_No",
    "Business_Or_Retention_Type",
]

def filter_metadata(metadata: dict) -> dict:
    return {
        k: metadata.get(k)
        for k in REQUIRED_FIELDS
        if metadata.get(k) not in ("", None)
    }

# ==============================
# HELPER: Detect Channel (STRICT)
# ==============================
def detect_channel_from_path(file_path: str):
    normalized_path = file_path.replace("\\", "/").lower()
    for channel in CHANNELS:
        if channel.lower() in normalized_path:
            return channel
    return None  # IMPORTANT: no "Unknown"

# ==============================
# HELPER: Move File (NO UNKNOWN)
# ==============================
def move_file_with_structure(src_path, target_root, base_folder, channel):
    rel_path = os.path.relpath(src_path, base_folder)
    rel_parts = rel_path.split(os.sep)

    # Remove channel folder if already present in source
    if channel and rel_parts and rel_parts[0].lower() == channel.lower():
        rel_parts = rel_parts[1:]

    # Build destination path
    if channel:
        target_path = os.path.join(target_root, channel, *rel_parts)
    else:
        target_path = os.path.join(target_root, *rel_parts)

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    shutil.move(src_path, target_path)

    print(f"Moved file to: {target_path}")

# ==============================
# PROCESS SINGLE PDF → DMS
# ==============================
def process_single_pdf(pdf_path: str) -> dict:
    try:
        if os.path.getsize(pdf_path) == 0:
            raise ValueError("PDF is empty")

        pdf_data = extract_text_from_pdf_via_svg_all_pages(pdf_path)
        text = pdf_data.get("full_text", "")

        if not text.strip():
            raise ValueError("No text extracted from PDF")

        metadata = extract_insurance_metadata(text)
        filtered_metadata = filter_metadata(metadata)
        print("Data Filtered data from pdf",filtered_metadata,"\n")
        if not filtered_metadata:
            raise ValueError("No valid metadata after filtering")

        channel = detect_channel_from_path(pdf_path)

        payload = {
            **filtered_metadata,
            "source_file": os.path.basename(pdf_path)
        }

        # Add channel only if detected
        if channel:
            payload["Channel"] = channel

        # DMS UPLOAD
        response = upload_document_to_dolphin_dms(
            file_path=pdf_path,
            policy_data=payload
        )

        payload["dms_response"] = response
        payload["channel"] = channel
        return payload

    except Exception as e:
        return {
            "source_file": os.path.basename(pdf_path),
            "channel": detect_channel_from_path(pdf_path),
            "error": str(e)
        }

# ==============================
# POST PROCESSING
# ==============================
def handle_post_processing(pdf_path, result, top_level_folder):
    channel = result.get("channel")

    if "error" in result:
        target_root = os.path.join(BASE_FOLDER_PATH, UNPROCESSED_FOLDER)
    else:
        target_root = os.path.join(BASE_FOLDER_PATH, PROCESSED_FOLDER)

    move_file_with_structure(pdf_path, target_root, top_level_folder, channel)

# ==============================
# WALK & PROCESS
# ==============================
def process_selected_folders(base_path, folders):
    for folder in folders:
        top_level = os.path.join(base_path, folder)

        if not os.path.exists(top_level):
            print(f"Missing folder: {top_level}")
            continue

        for root, _, files in os.walk(top_level):
            for file in files:
                if file.lower().endswith(".pdf"):
                    pdf_path = os.path.join(root, file)

                    print(f"\nProcessing: {pdf_path}")
                    result = process_single_pdf(pdf_path)

                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    handle_post_processing(pdf_path, result, top_level)

# ==============================
# MAIN
# ==============================
def main():
    process_selected_folders(BASE_FOLDER_PATH, PROCESS_FOLDERS)

if __name__ == "__main__":
    main()
