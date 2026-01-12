import os
import shutil
import streamlit as st
from main import process_single_pdf

# ==============================
# CONFIG
# ==============================
BASE_FOLDER_PATH = "./Folder_Structure"
TEMP_UPLOAD_DIR = "./temp_uploads"

os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

PROCESS_FOLDERS = [
    "Automatic_Preprocess",
    "Manual_Preprocess"
]

PROCESSED_FOLDER = "Process_Files"
UNPROCESSED_FOLDER = "Unprocess_Files"

# ==============================
# STREAMLIT UI
# ==============================
st.set_page_config(page_title="PDF Processing Dashboard", layout="wide")

st.title("📄 PDF Insurance Processing System")
st.markdown("Folder-based & local upload PDF processing with live progress tracking")

# ==============================
# SIDEBAR METRICS PLACEHOLDERS
# ==============================
sidebar_total = st.sidebar.empty()
sidebar_success = st.sidebar.empty()
sidebar_failed = st.sidebar.empty()

def update_sidebar(total=0, success=0, failed=0):
    sidebar_total.metric("Total Files", total)
    sidebar_success.metric("Processed Successfully", success)
    sidebar_failed.metric("Failed / Unprocessed", failed)

update_sidebar(0, 0, 0)

# ==============================
# SECTION 1: FOLDER INPUT
# ==============================
st.subheader("📁 Process PDFs From Folder")
root_folder = st.text_input("Enter Root Folder Path", value=BASE_FOLDER_PATH)
start_folder_btn = st.button("▶️ Start Folder Processing")

# ==============================
# SECTION 2: FILE UPLOAD
# ==============================
st.subheader("📤 Upload PDFs From Local Machine")
uploaded_files = st.file_uploader(
    "Upload PDF files",
    type=["pdf"],
    accept_multiple_files=True
)
start_upload_btn = st.button("▶️ Start Upload Processing")

# ==============================
# HELPER: COUNT PDFs
# ==============================
def count_pdfs(base_path, folders):
    count = 0
    for folder in folders:
        folder_path = os.path.join(base_path, folder)
        if not os.path.exists(folder_path):
            continue
        for _, _, files in os.walk(folder_path):
            count += len([f for f in files if f.lower().endswith(".pdf")])
    return count

# ==============================
# POST PROCESSING LOGIC (FIXED)
# ==============================
def handle_post_processing(pdf_path, result, root_folder):
    """
    SUCCESS  -> Process_Files/<SUBFOLDER>/file.pdf
    FAILURE  -> Unprocess_Files/<SUBFOLDER>/file.pdf

    Only preserves SUBFOLDER name
    """

    normalized = os.path.normpath(pdf_path)
    parts = normalized.split(os.sep)

    subfolder = None

    if "Automatic_Preprocess" in parts:
        idx = parts.index("Automatic_Preprocess")
        subfolder = parts[idx + 1] if len(parts) > idx + 1 else "Unknown"
    elif "Manual_Preprocess" in parts:
        idx = parts.index("Manual_Preprocess")
        subfolder = parts[idx + 1] if len(parts) > idx + 1 else "Unknown"
    else:
        # Uploaded files
        subfolder = "Uploaded"

    if "error" in result:
        dest_base = os.path.join(root_folder, UNPROCESSED_FOLDER)
    else:
        dest_base = os.path.join(root_folder, PROCESSED_FOLDER)

    dest_dir = os.path.join(dest_base, subfolder)
    os.makedirs(dest_dir, exist_ok=True)

    dest_path = os.path.join(dest_dir, os.path.basename(pdf_path))
    shutil.move(pdf_path, dest_path)

# ==============================
# COMMON PROCESSING FUNCTION
# ==============================
def process_with_progress(pdf_paths, root_folder):
    total_files = len(pdf_paths)
    processed = success = failed = 0

    update_sidebar(total_files, success, failed)
    progress_bar = st.progress(0)
    status_text = st.empty()

    for pdf_path in pdf_paths:
        file_name = os.path.basename(pdf_path)
        status_text.info(f"🔄 Processing: {file_name}")

        result = process_single_pdf(pdf_path)
        handle_post_processing(pdf_path, result, root_folder)

        processed += 1
        if "error" in result:
            failed += 1
        else:
            success += 1

        progress_bar.progress(processed / total_files)
        update_sidebar(total_files, success, failed)

        with st.expander(f"📄 Result: {file_name}", expanded=False):
            st.json(result)

    status_text.success("✅ Processing Completed!")

# ==============================
# FOLDER PROCESSING
# ==============================
if start_folder_btn:
    if not os.path.exists(root_folder):
        st.error("❌ Root folder does not exist")
        st.stop()

    total_files = count_pdfs(root_folder, PROCESS_FOLDERS)
    if total_files == 0:
        st.warning("⚠️ No PDF files found")
        st.stop()

    st.success(f"📂 Total PDFs Found: {total_files}")

    pdf_list = []
    for folder in PROCESS_FOLDERS:
        folder_path = os.path.join(root_folder, folder)
        if not os.path.exists(folder_path):
            continue
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".pdf"):
                    pdf_list.append(os.path.join(root, file))

    process_with_progress(pdf_list, root_folder)

# ==============================
# FILE UPLOAD PROCESSING
# ==============================
if start_upload_btn:
    if not uploaded_files:
        st.warning("⚠️ Please upload at least one PDF")
        st.stop()

    saved_paths = []
    for uploaded_file in uploaded_files:
        temp_path = os.path.join(TEMP_UPLOAD_DIR, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())
        saved_paths.append(temp_path)

    st.success(f"📤 Uploaded PDFs: {len(saved_paths)}")
    process_with_progress(saved_paths, root_folder)

    shutil.rmtree(TEMP_UPLOAD_DIR, ignore_errors=True)
    os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
