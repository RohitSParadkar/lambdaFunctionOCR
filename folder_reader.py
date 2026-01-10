
import os
import json
import shutil
from insertData import insert_json
from gemini_extractor import extract_insurance_metadata 
from img_xml_text_extractor import extract_text_from_pdf_via_svg_all_pages




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

def detect_channel_from_path(file_path: str) -> str:
    normalized_path = file_path.replace("\\", "/").lower()
    for channel in CHANNELS:
        if channel.lower() in normalized_path:
            return channel
    return "Unknown"

# ==============================
# HELPER: Move File Keeping Folder Structure
# ==============================
def move_file_with_structure(src_path: str, target_root: str, base_folder: str, channel: str):
    """
    Move file into target_root/channel/... preserving folder structure relative to base_folder,
    but avoid duplicating the channel folder.
    """
    # relative path of the file to the top-level folder
    rel_path = os.path.relpath(src_path, base_folder)

    # Split into parts
    rel_parts = rel_path.split(os.sep)

    # If the first folder in relative path is the same as channel, skip it
    if rel_parts and rel_parts[0].lower() == channel.lower():
        rel_parts = rel_parts[1:]  # remove first part

    # Full target path: target_root / channel / remaining relative path
    target_path = os.path.join(target_root, channel, *rel_parts)
    target_dir = os.path.dirname(target_path)

    os.makedirs(target_dir, exist_ok=True)

    # Move the file
    shutil.move(src_path, target_path)
    print(f"Moved file to: {target_path}")
# ==============================
# FUNCTION: Process single PDF
# ==============================
def process_single_pdf(pdf_path: str) -> dict:
    try:
        if os.path.getsize(pdf_path) == 0:
            raise ValueError("PDF file is empty (0 bytes)")

        pdf_result = extract_text_from_pdf_via_svg_all_pages(pdf_path)
        text = pdf_result.get("full_text", "")

        if not text.strip():
            raise ValueError("No text extracted from PDF")

        result = extract_insurance_metadata(text)

        result["source_file"] = os.path.basename(pdf_path)
        result["channel"] = detect_channel_from_path(pdf_path)

        return result

    except Exception as e:
        return {
            "source_file": os.path.basename(pdf_path),
            "channel": detect_channel_from_path(pdf_path),
            "error": str(e)
        }

# ==============================
# POST-PROCESSING: Move File
# ==============================
def handle_post_processing(pdf_path: str, result: dict, top_level_folder: str):
    channel = result.get("channel", "Unknown")

    if "error" in result:
        target_root = os.path.join(BASE_FOLDER_PATH, UNPROCESSED_FOLDER)
    else:
        target_root = os.path.join(BASE_FOLDER_PATH, PROCESSED_FOLDER)

    move_file_with_structure(pdf_path, target_root, top_level_folder, channel)

# ==============================
# FUNCTION: Recursively Process PDFs
# ==============================
def process_selected_folders(base_path: str, folders: list):
    for folder in folders:
        top_level_path = os.path.join(base_path, folder)

        if not os.path.exists(top_level_path):
            print(f"Folder not found: {top_level_path}")
            continue

        for root, dirs, files in os.walk(top_level_path):
            for file_name in files:
                if file_name.lower().endswith(".pdf"):
                    pdf_path = os.path.join(root, file_name)

                    print(f"\nProcessing: {pdf_path}")

                    result = process_single_pdf(pdf_path)
                    print(json.dumps(result, ensure_ascii=False, indent=2))

                    # Insert only successful records
                    if "error" not in result:
                        insert_json(result)

                    # Move file keeping folder structure relative to top-level folder
                    handle_post_processing(pdf_path, result, top_level_path)
