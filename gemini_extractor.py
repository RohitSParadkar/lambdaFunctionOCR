import json
import re
import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv


# =========================
# LOAD ENV (Lambda-safe)
# =========================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found in environment variables")



# FINAL DATABASE SCHEMA
# =========================
FINAL_SCHEMA = {
    "Policy_Number": "",
    "Insured_Name": "",
    "Insured_Contact_No": "",
    "Insurance_Company_Name": "",
    "Previous_Insurance_Company": "",
    "Products": "",
    "Policy_Start_Date": "",
    "Policy_Expiry_Date": "",
    "Sum_Assured_OR_IDV": "",
    "Net_Premium": "",
    "GST_Amount": "",
    "Total_Premium": "",
    "Vehicle_Registration_No": "",
    "Business_Or_Retention_Type": "",
    "Created_At": ""
}


ALLOWED_PRODUCTS = {
    "2w", "4w", "Contractors All Risk", "Critical Illness",
    "Cybersecurity", "Directors & Officers", "Erection All Risk",
    "Errors and Omissions", "Fidelity Guarantee", "Fire", "GCV",
    "GMC", "GPA", "GTL", "Health", "Home", "Industrial All Risk",
    "Life", "Marine", "OPD", "Others", "PA",
    "Professional Indemnity", "Super Topup", "Surety Bonds",
    "Trade Credit", "Travel", "Workmen Compensation"
}

ALLOWED_BUSINESS_TYPES = {
    "Fresh or New", "Renewal", "Rollover"
}

ALLOWED_INSURANCE_COMPANIES = {
    "ABHID", "ACKO", "Aditya Birla Health Insurance Company",
    "Aditya Birla Sun Life Insurance Company", "Bajaj Allianz",
    "BALIC", "Birla", "Care Health", "Chola MS",
    "CHOLAMANDALAM MS GENERAL", "Future Generali", "GO DIGIT",
    "HDFC Ergo", "HDFC Life", "ICICI Lombard", "ICICI Pru",
    "Iffco Tokio", "Indusind Nippon", "Kotak Zurich", "Liberty",
    "Magma General", "Magma HDI", "Manipal Cigna", "NATIONAL",
    "National Insurance", "New India", "Niva Bupa", "ORIENTAL",
    "Oriental Insurance", "Reliance General", "Reliance GI",
    "Royal Sundaram", "SBI General", "Shriram General",
    "Shriram Life", "Star Health", "TATA AIA", "TATA AIG",
    "United India", "Sompo", "UIGC"
}


# =========================
# GEMINI CONFIG
# =========================
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL_NAME}:generateContent"
)


def call_gemini(prompt: str) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        headers=headers,
        data=json.dumps(payload),
        timeout=60
    )

    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


# =========================
# METADATA EXTRACTION
# =========================
def extract_insurance_metadata(text: str) -> dict:
    prompt = f"""
Extract insurance policy information.

STRICT RULES:
- Output ONLY valid JSON
- No markdown, no explanation
- Missing values must be empty ""
- Dates in DD/MM/YYYY only

PRODUCT RULES:
- Select ONE allowed product only
- "Motor" is INVALID

Allowed Products:
{sorted(ALLOWED_PRODUCTS)}

Allowed Insurance Companies:
{sorted(ALLOWED_INSURANCE_COMPANIES)}

JSON FORMAT:
{{
  "Policy_Number": "",
  "Insured_Name": "",
  "Insured_Contact_No": "",
  "Insurance_Company_Name": "",
  "Previous_Insurance_Company": "",
  "Products": "",
  "Policy_Start_Date": "",
  "Policy_Expiry_Date": "",
  "Sum_Assured_OR_IDV": "",
  "Net_Premium": "",
  "GST_Amount": "",
  "Vehicle_Registration_No": ""
}}

Document text:
{text}
"""

    raw = call_gemini(prompt).strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        data = FINAL_SCHEMA.copy()
    else:
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            data = FINAL_SCHEMA.copy()

    # Ensure all keys exist
    for key in FINAL_SCHEMA:
        data.setdefault(key, "")

    # Enforce allowed values
    if data["Products"] not in ALLOWED_PRODUCTS:
        data["Products"] = ""

    if data["Insurance_Company_Name"] not in ALLOWED_INSURANCE_COMPANIES:
        data["Insurance_Company_Name"] = ""

    if data["Previous_Insurance_Company"] not in ALLOWED_INSURANCE_COMPANIES:
        data["Previous_Insurance_Company"] = ""

    # Health insurance rule
    if data["Products"] == "Health":
        data["Vehicle_Registration_No"] = ""

    # =========================
    # BUSINESS TYPE LOGIC
    # =========================
    prev = data["Previous_Insurance_Company"]
    curr = data["Insurance_Company_Name"]

    if not prev:
        data["Business_Or_Retention_Type"] = "Fresh or New"
    elif prev == curr:
        data["Business_Or_Retention_Type"] = "Renewal"
    else:
        data["Business_Or_Retention_Type"] = "Rollover"

    # =========================
    # TOTAL PREMIUM CALCULATION
    # =========================
    def to_float(value):
        try:
            return float(re.sub(r"[^\d.]", "", value))
        except Exception:
            return 0.0

    net = to_float(data["Net_Premium"])
    gst = to_float(data["GST_Amount"])

    data["Total_Premium"] = str(round(net + gst, 2)) if net or gst else ""

    data["Created_At"] = datetime.now(timezone.utc).astimezone().isoformat()

    return data
