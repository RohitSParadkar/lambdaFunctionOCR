import os
import requests
from pathlib import Path
from typing import Dict
import urllib3
from datetime import datetime, timezone
from dotenv import load_dotenv

# =========================
# LOAD ENV
# =========================
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# =========================
# INTERNAL SESSION FACTORY
# =========================
def _get_dms_session(verify_ssl: bool = False) -> requests.Session:
    session = requests.Session()
    session.auth = (
        os.getenv("DMS_USERNAME"),
        os.getenv("DMS_PASSWORD"),
    )
    session.verify = verify_ssl
    return session


# =========================
# UPLOAD DOCUMENT (SAFE)
# =========================
def upload_document_to_dolphin_dms(
    file_path: str,
    policy_data: Dict,
    verify_ssl: bool = False,
) -> Dict:
    """
    Upload document to Dolphin DMS

    SUCCESS:
    {
      "status": "SUCCESS",
      "response": {...}
    }

    ERROR:
    {
      "status": "FAILED",
      "error": "...",
      "stage": "upload_document_to_dolphin_dms",
      "created_at": ISO_DATETIME
    }
    """

    try:
        host_url = os.getenv("HOST_URL")
        company_id = os.getenv("COMPANY_ID")

        if not host_url or not company_id:
            raise EnvironmentError("HOST_URL or COMPANY_ID not set")

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

            return {
                "status": "SUCCESS",
                "response": response.json()
            }

        finally:
            session.close()

    except requests.exceptions.Timeout:
        return {
            "status": "FAILED",
            "error": "DMS upload timeout",
            "stage": "upload_document_to_dolphin_dms",
            "created_at": datetime.now(timezone.utc).astimezone().isoformat()
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "FAILED",
            "error": f"DMS request failed: {str(e)}",
            "stage": "upload_document_to_dolphin_dms",
            "created_at": datetime.now(timezone.utc).astimezone().isoformat()
        }

    except Exception as e:
        return {
            "status": "FAILED",
            "error": str(e),
            "stage": "upload_document_to_dolphin_dms",
            "created_at": datetime.now(timezone.utc).astimezone().isoformat()
        }


# =========================
# DOWNLOAD DOCUMENT (SAFE)
# =========================
def download_document_from_dolphin_dms(
    mongo_id: str,
    save_path: str,
    verify_ssl: bool = False,
) -> Dict:
    """
    Download document from Dolphin DMS

    SUCCESS:
    { "status": "SUCCESS" }

    ERROR:
    {
      "status": "FAILED",
      "error": "...",
      "stage": "download_document_from_dolphin_dms",
      "created_at": ISO_DATETIME
    }
    """

    try:
        host_url = os.getenv("HOST_URL")
        company_id = os.getenv("COMPANY_ID")

        if not host_url or not company_id:
            raise EnvironmentError("HOST_URL or COMPANY_ID not set")

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

            return {
                "status": "SUCCESS",
                "file_path": save_path
            }

        finally:
            session.close()

    except requests.exceptions.Timeout:
        return {
            "status": "FAILED",
            "error": "DMS download timeout",
            "stage": "download_document_from_dolphin_dms",
            "created_at": datetime.now(timezone.utc).astimezone().isoformat()
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "FAILED",
            "error": f"DMS request failed: {str(e)}",
            "stage": "download_document_from_dolphin_dms",
            "created_at": datetime.now(timezone.utc).astimezone().isoformat()
        }

    except Exception as e:
        return {
            "status": "FAILED",
            "error": str(e),
            "stage": "download_document_from_dolphin_dms",
            "created_at": datetime.now(timezone.utc).astimezone().isoformat()
        }
