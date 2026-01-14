import json
import re
import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from token_counter import gemini_token_and_generate

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
    "Gross_or_Total_Premium": "",
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
    # UPDATED PROMPT: Added specific "Proposer" detection and emphasized raw text for mobile
    prompt = f"""
Extract insurance policy information from the document text provided below.

STRICT FIELD RULES:
1. Insured_Contact_No: This is often labeled as "Proposer Mobile Number", "Mobile No", "Contact No", or "Phone". 
   - Extract the value EXACTLY as it appears in the text. 
   - DO NOT remove spaces, plus signs (+), or asterisks (*). 
   - DO NOT apply any validation or formatting rules. 
   - Example: If text says "+91 87**43**67", you must return "+91 87**43**67".
2. Insured_Name: Often labeled as "Proposer Name" or "Name of Insured".
3. Dates: Use DD/MM/YYYY format only.
4. Output: ONLY valid JSON. No markdown (no ```json).
5. Premium Rules (VERY IMPORTANT):
   - Net_Premium:
     • This is the BASE premium amount.
     • It MUST EXCLUDE all taxes such as GST, CGST, SGST, IGST, Cess, or any other charges.
     • If the document shows labels like "Net Premium", "Basic Premium", or "Premium (Excl. Tax)", extract this value here.

   - Gross_or_Total_Premium:
     • This is the FINAL payable premium amount.
     • It MUST be Net_Premium PLUS all applicable taxes (GST / CGST / SGST / IGST / Cess).
     • If the document shows labels like "Gross Premium", "Total Premium", "Premium Payable", or "Total Amount", extract this value here.

   - If only ONE premium value is present in the document:
     • If it includes tax → put it in Gross_or_Total_Premium only.
     • If it excludes tax → put it in Net_Premium only.
6. Amount Formatting Rules (STRICT):
   - For Net_Premium, Gross_or_Total_Premium, and Sum_Assured_OR_IDV:
     • Return ONLY numeric values.
     • DO NOT include currency symbols (₹, Rs., INR).
     • DO NOT include commas (,).
     • DO NOT include suffixes like "/-", "-/", or any non-numeric characters.
     • Decimal point (.) is allowed only if present in the document.
     • Example:
       - "Rs. 13,577/-" → "13577"
       - "11,506.00" → "11506.00"
       - "5,00,000/-" → "500000"

===========================================================
PRODUCT CLASSIFICATION GUIDE:
- Private Car / Car / Passenger Vehicle -> "4w"
- Two Wheeler / Bike / Scooter / Motor Cycle -> "2w"
- Commercial Vehicle / Truck / GCV / Lorry -> "GCV"
- Mediclaim / Individual Health / Family Floater -> "Health"
- Group Medical / GMC / Corporate Health -> "GMC"
- Personal Accident (Individual) -> "PA"
- Group Personal Accident -> "GPA"
- Term Life / Individual Life -> "Life"
- Group Term Life -> "GTL"
- SFSP / Standard Fire / Fire & Perils -> "Fire"
- Workmen Compensation / WC -> "Workmen Compensation"
- Professional Indemnity / E&O -> "Professional Indemnity"
- CAR / EAR / IAR -> "Contractors All Risk" / "Erection All Risk" / "Industrial All Risk"

===========================================================
INSURANCE COMPANY NORMALIZATION RULES:
If the document contains any FULL FORM or VARIANT name, convert it to the STANDARD SHORT NAME below:

- "Universal Sompo General Insurance Company Limited" → "Sompo"
- "Universal Sompo General Insurance" → "Sompo"
IMPORTANT INSURANCE COMPANY DISAMBIGUATION RULES (STRICT):

- If the document explicitly mentions:
  • "TATA AIA", "TATA AIA Life", or "TATA AIA Life Insurance"
    → Return EXACTLY "TATA AIA"

  • "TATA AIG", "TATA AIG General Insurance", or "TATA AIG Insurance"
    → Return EXACTLY "TATA AIG"

- DO NOT confuse "TATA AIA" with "TATA AIG".
- DO NOT guess between AIA and AIG.
- If both words "AIA" and "AIG" appear, choose the one that appears NEAREST to the word "Insurance".

- Product-based validation:
  • Life, GTL → Prefer "TATA AIA"
  • Health, Motor, Fire, Marine, PA → Prefer "TATA AIG"

- If the company name cannot be confidently determined:
  → Leave Insurance_Company_Name EMPTY ("")

Always return the standardized name ONLY from the Allowed Insurance Companies list.

===========================================================

Allowed Products List:
{sorted(ALLOWED_PRODUCTS)}

Allowed Insurance Companies:
{sorted(ALLOWED_INSURANCE_COMPANIES)}

===========================================================
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
  "Gross_or_Total_Premium": "",
  "Vehicle_Registration_No": ""
}}

Document text:
{text}
"""
    token_info = gemini_token_and_generate(prompt)
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

    # Validation and Product Logic
    if data["Products"] not in ALLOWED_PRODUCTS:
        data["Products"] = ""

    health_related = ["Health", "GMC", "GPA", "GTL", "Life", "Critical Illness", "Super Topup"]
    if data["Products"] in health_related:
        data["Vehicle_Registration_No"] = ""

    # Business Type Logic
    prev = data["Previous_Insurance_Company"]
    curr = data["Insurance_Company_Name"]
    if not prev:
        data["Business_Or_Retention_Type"] = "Fresh or New"
    elif prev == curr:
        data["Business_Or_Retention_Type"] = "Renewal"
    else:
        data["Business_Or_Retention_Type"] = "Rollover"

    data["Created_At"] = datetime.now(timezone.utc).astimezone().isoformat()
    data["_token_usage"] = token_info["usage_metadata"]

    return data

