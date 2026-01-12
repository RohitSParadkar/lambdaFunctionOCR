import os
import shutil
import time
import streamlit as st
from dotenv import load_dotenv
from main import process_single_pdf

# ==============================
# LOAD ENV
# ==============================
load_dotenv()

STREAMLIT_USERNAME = os.getenv("STREAMLIT_USERNAME")
STREAMLIT_PASSWORD = os.getenv("STREAMLIT_PASSWORD")

if not STREAMLIT_USERNAME or not STREAMLIT_PASSWORD:
    st.error("❌ STREAMLIT_USERNAME or STREAMLIT_PASSWORD not set in .env")
    st.stop()

# ==============================
# APP CONFIG
# ==============================
BASE_FOLDER_PATH = "./Folder_Structure"

PROCESS_FOLDERS = [
    "Automatic_Preprocess",
    "Manual_Preprocess"
]

PROCESSED_FOLDER = "Process_Files"
UNPROCESSED_FOLDER = "Unprocess_Files"

st.set_page_config(
    page_title="PDF Processing Dashboard",
    layout="wide"
)

# ==============================
# SESSION STATE INIT
# ==============================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "processing_times" not in st.session_state:
    st.session_state.processing_times = []

# ==============================
# LOGIN PAGE
# ==============================
def login_page():
    st.title("🔐 Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")

        if login_btn:
            if username == STREAMLIT_USERNAME and password == STREAMLIT_PASSWORD:
                st.session_state.authenticated = True
                st.success("✅ Login successful")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

# ==============================
# LOGOUT
# ==============================
def logout():
    st.session_state.authenticated = False

# ==============================
# DASHBOARD
# ==============================
def dashboard():

    st.title("📄 PDF Insurance Processing System")
    st.markdown("Folder-based PDF processing with live progress, timing & ETA")

    st.sidebar.button("🚪 Logout", on_click=logout)

    # ==============================
    # SIDEBAR METRICS
    # ==============================
    sidebar_total = st.sidebar.empty()
    sidebar_success = st.sidebar.empty()
    sidebar_failed = st.sidebar.empty()

    def update_sidebar(total=0, success=0, failed=0):
        sidebar_total.metric("Total Files", total)
        sidebar_success.metric("Processed Successfully", success)
        sidebar_failed.metric("Failed / Unprocessed", failed)

    update_sidebar()

    # ==============================
    # TIME METRICS (BELOW COUNTS)
    # ==============================
    with st.container():
        col1, col2 = st.columns(2)
        last_time_ph = col1.empty()
        avg_time_ph = col2.empty()

    def update_time_metrics(last_time=None):
        times = st.session_state.processing_times
        avg_time = sum(times) / len(times) if times else 0

        if last_time is not None:
            last_time_ph.metric(
                "⏱️ Last PDF Time (sec)",
                f"{last_time:.2f}"
            )

        avg_time_ph.metric(
            "📊 Average Time / PDF (sec)",
            f"{avg_time:.2f}"
        )

    update_time_metrics()

    # ==============================
    # FOLDER INPUT
    # ==============================
    st.subheader("📁 Process PDFs From Folder")
    root_folder = st.text_input("Enter Root Folder Path", value=BASE_FOLDER_PATH)
    start_folder_btn = st.button("▶️ Start Folder Processing")

    # ==============================
    # COUNT PDFs
    # ==============================
    def count_pdfs(base_path, folders):
        count = 0
        for folder in folders:
            folder_path = os.path.join(base_path, folder)
            if not os.path.exists(folder_path):
                continue
            for _, _, files in os.walk(folder_path):
                count += sum(f.lower().endswith(".pdf") for f in files)
        return count

    # ==============================
    # POST PROCESSING
    # ==============================
    def handle_post_processing(pdf_path, result, root_folder):
        normalized = os.path.normpath(pdf_path)
        parts = normalized.split(os.sep)

        if "Automatic_Preprocess" in parts:
            subfolder = parts[parts.index("Automatic_Preprocess") + 1]
        elif "Manual_Preprocess" in parts:
            subfolder = parts[parts.index("Manual_Preprocess") + 1]
        else:
            subfolder = "Unknown"

        if "error" in result:
            dest_base = os.path.join(root_folder, UNPROCESSED_FOLDER)
        else:
            dest_base = os.path.join(root_folder, PROCESSED_FOLDER)

        dest_dir = os.path.join(dest_base, subfolder)
        os.makedirs(dest_dir, exist_ok=True)

        shutil.move(
            pdf_path,
            os.path.join(dest_dir, os.path.basename(pdf_path))
        )

    # ==============================
    # PROCESS WITH PROGRESS + ETA
    # ==============================
    def process_with_progress(pdf_paths, root_folder):
        total_files = len(pdf_paths)
        success = failed = 0

        st.session_state.processing_times.clear()

        update_sidebar(total_files, success, failed)

        progress_bar = st.progress(0)
        progress_text = st.empty()
        eta_text = st.empty()
        status = st.empty()

        batch_start_time = time.time()

        for i, pdf_path in enumerate(pdf_paths, start=1):
            file_name = os.path.basename(pdf_path)
            status.info(f"🔄 Processing: {file_name}")

            file_start = time.time()

            result = process_single_pdf(pdf_path)

            file_time = time.time() - file_start
            st.session_state.processing_times.append(file_time)

            handle_post_processing(pdf_path, result, root_folder)

            if "error" in result:
                failed += 1
            else:
                success += 1

            # ==============================
            # PROGRESS UPDATE
            # ==============================
            progress = i / total_files
            progress_bar.progress(progress)

            percent = int(progress * 100)
            elapsed = time.time() - batch_start_time
            avg_time = elapsed / i
            remaining = avg_time * (total_files - i)

            progress_text.markdown(
                f"**Progress:** {percent}% &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"**File:** {i} / {total_files}"
            )

            eta_text.markdown(
                f"⏳ **ETA Remaining:** {int(remaining)} sec"
            )

            update_sidebar(total_files, success, failed)
            update_time_metrics(last_time=file_time)

            with st.expander(f"📄 Result: {file_name}"):
                st.write(f"⏱️ **Time Taken:** `{file_time:.2f} seconds`")
                st.json(result)

        status.success("✅ Processing Completed!")

    # ==============================
    # START PROCESS
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
# ROUTER
# ==============================
if st.session_state.authenticated:
    dashboard()
else:
    login_page()
