import re
THREE_WHEELER_KEYWORDS = [
    "auto rickshaw", "autorickshaw",
]

PASSENGER_KEYWORDS = [
    "passenger carrying", "pccv", "passenger vehicle",
]

NA_VARIANTS = {
    "na", "n.a", "n.a.", "n/a", "nil", "none", "not applicable", "not available","UNKNOWN","Jio Insurance Broking Ltd","Jio Insurance"
}
# =============================================================================
# CANONICAL KEY → LIST OF SHORTFORMS / ALIASES
# Fill in the values as needed — keys are from ALLOWED_INSURANCE_COMPANIES
# =============================================================================
INSURER_SHORTFORM_MAP = {
    "ABHID"                                  : ["Aditya Birla Health Insurance"],
    "ACKO"                                   : [],
    "Aditya Birla Health Insurance Company"  : [],
    "Aditya Birla Sun Life Insurance Company": [],
    "Bajaj Allianz"                          : ["Bajaj Allianz General Insurance Co Ltd."],
    "BALIC"                                  : [],
    "Birla"                                  : [],
    "Care Health"                            : ["Care Health Insurance Limited"],
    "Chola MS"                               : [],
    "CHOLAMANDALAM MS GENERAL"               : [],
    "Future Generali"                        : ["Future Generali India Insurance Co. Ltd."],
    "GO DIGIT"                               : ["Go Digit General Insurance Limited"],
    "HDFC Ergo"                              : [],
    "HDFC Life"                              : ["HDFC Life Insurance Co. Ltd."],
    "ICICI Lombard"                          : ["ICICI Lombard Health Care"],
    "ICICI Pru"                              : [],
    "Iffco Tokio"                            : [],
    "Indusind Nippon"                        : [],
    "Kotak Zurich"                           : ["Zurich Kotak General Insurance Company Limited"],
    "Liberty"                                : [],
    "Magma General"                          : [],
    "Magma HDI"                              : [],
    "Manipal Cigna"                          : [],
    "NATIONAL"                               : [],
    "National Insurance"                     : [],
    "New India"                              : ["THE NEW INDIA ASSURANCE COMPANY LTD."],
    "Niva Bupa"                              : ["Niva Bupa Health Insurance Company Limited","Niva Bupa Health Insurance"],
    "ORIENTAL"                               : [],
    "Oriental Insurance"                     : [],
    "Reliance General"                       : [],
    "Reliance GI"                            : [],
    "Royal Sundaram"                         : ["Royal Sundaram General Insurance Co. Limited","ROYALSUNDARAMGENERALINSURANCECO.LIMITED"],
    "SBI General"                            : [],
    "Shriram General"                        : [],
    "Shriram Life"                           : [],
    "Star Health"                            : ["Star Health And Allied Insurance Company Limited"],
    "TATA AIA"                               : [],
    "TATA AIG"                               : [],
    "United India"                           : [],
    "Sompo"                                  : [],
    "UIGC"                                   : [],
}


# OVERRIDE FUNCTION
# =============================================================================
def override_previous_insurer(data: dict) -> dict:
    """
    Step 1 — NA check:
        If Previous_Insurance_Company is NA / N.A / nil / etc.
          → clear Previous_Insurance_Company to ""
          → set Business_Or_Retention_Type = "Fresh or New"
          → return immediately

    Step 2 — Alias lookup:
        Search each alias list (values) in INSURER_SHORTFORM_MAP.
        If Previous_Insurance_Company found in any alias list
          → override with that list's key (canonical name)
        If not found
          → return data unchanged

    Args:
        data : parsed output dict

    Returns:
        data dict with corrections applied
    """
    previous = (data.get("Previous_Insurance_Company") or "").strip()

    if not previous:
        return data

    # Step 1: NA check
    previous_clean = re.sub(r'[^a-zA-Z]', '', previous).lower()

    na_clean = {re.sub(r'[^a-zA-Z]', '', v).lower() for v in NA_VARIANTS}

    if previous_clean in na_clean:
        data["Previous_Insurance_Company"] = ""
        data["Business_Or_Retention_Type"] = "Fresh or New"
        return data
    # Step 2: Alias lookup — find value, return key
    previous_lower = previous.lower()

    for canonical, aliases in INSURER_SHORTFORM_MAP.items():
        if previous_lower in [alias.strip().lower() for alias in aliases]:
            data["Previous_Insurance_Company"] = canonical
            return data

    return data

def override_pccv_3w(data: dict, raw_text: str) -> dict:
    """
    Checks if the document is a PCCV 3-wheeler (capacity <= 6).
    If yes → sets Products = "PCV".
    If no  → returns data unchanged.
    """
    text_lower = raw_text.lower()

    is_three_wheeler = any(kw in text_lower for kw in THREE_WHEELER_KEYWORDS)
    is_passenger     = any(kw in text_lower for kw in PASSENGER_KEYWORDS)

    if is_three_wheeler and is_passenger:
        data["Products"] = "PCV"

    return data