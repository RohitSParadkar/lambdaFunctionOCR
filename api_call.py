import os
import requests
from pathlib import Path
from typing import Dict
import urllib3
from dotenv import load_dotenv

# =========================
# LOAD ENV
# =========================
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _get_dms_session(verify_ssl: bool = False) -> requests.Session:
    """
    Internal helper to create an authenticated DMS session
    """
    session = requests.Session()
    session.auth = (
        os.getenv("DMS_USERNAME"),
        os.getenv("DMS_PASSWORD"),
    )
    session.verify = verify_ssl
    return session


def upload_document_to_dolphin_dms(
    file_path: str,
    policy_data: Dict,
    verify_ssl: bool = False,
) -> Dict:
    """
    Upload document to Dolphin DMS

    Returns API response (contains 'Mongo ID' on success)
    """
    host_url = os.getenv("HOST_URL")
    company_id = os.getenv("COMPANY_ID")

    if not all([host_url, company_id]):
        raise ValueError("HOST_URL and COMPANY_ID must be set in environment")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    url = f"{host_url.rstrip('/')}/api/docprocessing/document/"

    params = {
        "companyId": company_id,
        "fileName": Path(file_path).name,
        **policy_data,
    }

    session = _get_dms_session(verify_ssl)

    try:
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f)}
            response = session.post(
                url,
                params=params,
                files=files,
                timeout=60,
            )

        response.raise_for_status()
        return response.json()

    finally:
        session.close()


def download_document_from_dolphin_dms(
    mongo_id: str,
    save_path: str,
    verify_ssl: bool = False,
) -> None:
    """
    Download document from Dolphin DMS using Mongo ID
    """
    host_url = os.getenv("HOST_URL")
    company_id = os.getenv("COMPANY_ID")

    if not all([host_url, company_id]):
        raise ValueError("HOST_URL and COMPANY_ID must be set in environment")

    url = f"{host_url.rstrip('/')}/download.do/{mongo_id}/{company_id}"

    session = _get_dms_session(verify_ssl)

    try:
        response = session.get(url, stream=True, timeout=60)
        response.raise_for_status()

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(8192):
                if chunk:
                    f.write(chunk)
    finally:
        session.close()
