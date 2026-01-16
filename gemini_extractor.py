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

if not MODEL_NAME:
    raise EnvironmentError("MODEL_NAME not found in environment variables")

# =========================
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

# =========================
# ALLOWED VALUES
# =========================
ALLOWED_PRODUCTS = {
    "2w", "4w", "Contractors All Risk", "Critical Illness",
    "Cybersecurity", "Directors & Officers", "Erection All Risk",
    "Errors and Omissions", "Fidelity Guarantee", "Fire", "GCV",
    "GMC", "GPA", "GTL", "Health", "Home", "Industrial All Risk",
    "Life", "Marine", "OPD", "Others", "PA",
    "Professional Indemnity", "Super Topup", "Surety Bonds",
    "Trade Credit", "Travel", "Workmen Compensation","PCV",
    "Miscellaneous"
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

# =========================
# GEMINI API CALL
# =========================
def call_gemini(prompt: str) -> str:
    try:
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

    except requests.exceptions.Timeout:
        raise RuntimeError("Gemini API timeout")

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Gemini API request failed: {str(e)}")

    except (KeyError, IndexError):
        raise RuntimeError("Unexpected Gemini response structure")

# =========================
# METADATA EXTRACTION
# =========================
def extract_insurance_metadata(text: str) -> dict:
    try:
        if not text or not text.strip():
            raise ValueError("Empty document text")

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
PRODUCT CLASSIFICATION GUIDE (STRICT PRIORITY ORDER):

IMPORTANT:
- If BOTH "Passenger" AND "Commercial" appear → TREAT AS PASSENGER VEHICLE (PCV)
- Passenger classification ALWAYS OVERRIDES GCV

1. Passenger Carrying Vehicle:
   - Keywords: Passenger, Taxi, Cab, Auto, Bus, School Bus, Staff Bus, PCCV
   → "PCV"
- Private Car / Car / Passenger Vehicle -> "4w"
- Two Wheeler / Bike / Scooter / Motor Cycle -> "2w"
- Commercial Vehicle / Truck / GCV / Lorry -> "GCV"
- Mediclaim / Individual Health / Family Floater -> "Health"
- Group Medical / GMC / Corporate Health -> "GMC"
- Personal Accident (Individual) -> "PA"
- Group Personal Accident -> "GPA"
- Term Life / Individual Life -> "Life"
- Passenger Carrying Vehicle /PCCV - > "PCV"
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
BUSINESS / RETENTION TYPE RULES (STRICT):

You MUST determine Business_Or_Retention_Type directly from the document text.

Allowed values ONLY:
- "Fresh or New"
- "Renewal"
- "Rollover"

Rules:
1. "Fresh or New":
   - No previous insurer mentioned
   - First time insurance
   - New vehicle / new policy
   - Keywords: New Business, Fresh Policy, First Policy

2. "Renewal":
   - Previous insurer is SAME as current insurer
   - Keywords: Renewal, Renewed with same insurer, Expiring Policy (same company)

3. "Rollover":
   - Previous insurer is DIFFERENT from current insurer
   - Keywords: Rollover, Ported, Transferred, Previous Insurance Company mentioned

IMPORTANT:
- Use DOCUMENT CONTEXT, not assumptions
- DO NOT infer based on missing data
- If unsure, choose the MOST LOGICAL option from the text
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
  "Business_Or_Retention_Type":"",
  "Vehicle_Registration_No": ""
}}

Document text:
{text}
"""

        # Token tracking
        token_info = gemini_token_and_generate(prompt)

        # Gemini call
        raw = call_gemini(prompt)
        raw = raw.replace("```json", "").replace("```", "").strip()

        # JSON extraction
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in Gemini response")

        data = json.loads(match.group())

        # Ensure schema completeness
        for key in FINAL_SCHEMA:
            data.setdefault(key, "")

        # Product validation
        if data["Products"] not in ALLOWED_PRODUCTS:
            data["Products"] = ""

        # Health-related cleanup
        health_related = {
            "Health", "GMC", "GPA", "GTL",
            "Life", "Critical Illness", "Super Topup"
        }

        if data["Products"] in health_related:
            data["Vehicle_Registration_No"] = ""

        data["Created_At"] = datetime.now(timezone.utc).astimezone().isoformat()
        data["_token_usage"] = token_info.get("usage_metadata", {})

        return data

    except Exception as e:
        return {
            "error": str(e),
            "stage": "extract_insurance_metadata",
            "Created_At": datetime.now(timezone.utc).astimezone().isoformat()
        }
