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
    st.error("STREAMLIT_USERNAME or STREAMLIT_PASSWORD not set")
    st.stop()

# ==============================
# APP CONFIG
# ==============================
BASE_FOLDER_PATH = "./Folder_Structure"

PROCESS_FOLDERS = ["Automatic_Preprocess", "Manual_Preprocess"]
PROCESSED_FOLDER = "Process_Files"
UNPROCESSED_FOLDER = "Unprocess_Files"

st.set_page_config(
    page_title="PDF Processing Dashboard",
    layout="wide"
)

# ==============================
# SESSION STATE
# ==============================
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("processing_times", [])

# ==============================
# LOGIN
# ==============================
def login_page():
    st.title("🔐 Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if username == STREAMLIT_USERNAME and password == STREAMLIT_PASSWORD:
                st.session_state.authenticated = True
                st.success("✅ Login successful")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

def logout():
    st.session_state.authenticated = False
    st.rerun()

# ==============================
# DASHBOARD
# ==============================
def dashboard():
    st.title("📄 PDF Insurance Processing System")
    st.markdown("Folder-based processing with live progress, timing & ETA")

    st.sidebar.button("🚪 Logout", on_click=logout)

    # ------------------------------
    # SIDEBAR METRICS
    # ------------------------------
    total_ph = st.sidebar.empty()
    success_ph = st.sidebar.empty()
    failed_ph = st.sidebar.empty()

    def update_sidebar(total=0, success=0, failed=0):
        total_ph.metric("Total Files", total)
        success_ph.metric("Success", success)
        failed_ph.metric("Failed", failed)

    update_sidebar()

    # ------------------------------
    # TIME METRICS
    # ------------------------------
    col1, col2 = st.columns(2)
    last_time_ph = col1.empty()
    avg_time_ph = col2.empty()

    def update_time_metrics(last_time=None):
        times = st.session_state.processing_times
        avg = sum(times) / len(times) if times else 0

        if last_time is not None:
            last_time_ph.metric("⏱️ Last PDF (sec)", f"{last_time:.2f}")

        avg_time_ph.metric("📊 Avg / PDF (sec)", f"{avg:.2f}")

    update_time_metrics()

    # ------------------------------
    # FOLDER INPUT
    # ------------------------------
    st.subheader("📁 Process PDFs From Folder")
    root_folder = st.text_input("Root Folder Path", BASE_FOLDER_PATH)
    start_btn = st.button("▶️ Start Processing")

    # ------------------------------
    # COUNT PDFs
    # ------------------------------
    def count_pdfs(base_path):
        count = 0
        for folder in PROCESS_FOLDERS:
            path = os.path.join(base_path, folder)
            for _, _, files in os.walk(path):
                count += sum(f.lower().endswith(".pdf") for f in files)
        return count

    # ------------------------------
    # FILE MOVE (POST PROCESS)
    # ------------------------------
    def handle_post_processing(pdf_path, result, root_folder):
        dest_root = (
            PROCESSED_FOLDER
            if result["status"] == "SUCCESS"
            else UNPROCESSED_FOLDER
        )

        channel = result.get("channel")
        base_dest = os.path.join(root_folder, dest_root)

        if channel:
            base_dest = os.path.join(base_dest, channel)

        os.makedirs(base_dest, exist_ok=True)

        shutil.move(
            pdf_path,
            os.path.join(base_dest, os.path.basename(pdf_path))
        )

    # ------------------------------
    # PROCESS WITH PROGRESS
    # ------------------------------
    def process_with_progress(pdf_paths):
        total = len(pdf_paths)
        success = failed = 0

        st.session_state.processing_times.clear()
        update_sidebar(total, success, failed)

        progress_bar = st.progress(0)
        progress_txt = st.empty()
        eta_txt = st.empty()
        status_txt = st.empty()

        start_time = time.time()

        for idx, pdf_path in enumerate(pdf_paths, start=1):
            name = os.path.basename(pdf_path)
            status_txt.info(f"🔄 Processing: {name}")

            t0 = time.time()
            result = process_single_pdf(pdf_path)
            elapsed = time.time() - t0

            st.session_state.processing_times.append(elapsed)
            handle_post_processing(pdf_path, result, root_folder)

            if result["status"] == "SUCCESS":
                success += 1
            else:
                failed += 1

            progress = idx / total
            progress_bar.progress(progress)

            avg_time = (time.time() - start_time) / idx
            remaining = avg_time * (total - idx)

            progress_txt.markdown(
                f"**Progress:** {int(progress * 100)}% | "
                f"**File:** {idx}/{total}"
            )

            eta_txt.markdown(f"⏳ ETA: `{int(remaining)} sec`")

            update_sidebar(total, success, failed)
            update_time_metrics(elapsed)

            with st.expander(f"📄 Result: {name}"):
                st.write(f"⏱️ Time Taken: `{elapsed:.2f} sec`")
                st.json(result)

        status_txt.success("✅ Processing Completed")

    # ------------------------------
    # START BUTTON
    # ------------------------------
    if start_btn:
        if not os.path.exists(root_folder):
            st.error("❌ Root folder does not exist")
            st.stop()

        total = count_pdfs(root_folder)
        if total == 0:
            st.warning("⚠️ No PDFs found")
            st.stop()

        st.success(f"📂 Total PDFs Found: {total}")

        pdfs = []
        for folder in PROCESS_FOLDERS:
            path = os.path.join(root_folder, folder)
            for root, _, files in os.walk(path):
                for f in files:
                    if f.lower().endswith(".pdf"):
                        pdfs.append(os.path.join(root, f))

        process_with_progress(pdfs)

# ==============================
# ROUTER
# ==============================
if st.session_state.authenticated:
    dashboard()
else:
    login_page()
