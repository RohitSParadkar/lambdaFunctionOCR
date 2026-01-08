from img_xml_text_extractor import extract_text_from_pdf_via_svg_all_pages
from gemini_extractor import extract_insurance_metadata
import json

def main():
    """
    Provide the file path from local system in below variable
    Example:
    PDF_PATH = "./data/10000*****.pdf (url from local data directory)
    """
    PDF_PATH = "./data/test_data/data/motorData/Go_Digital/DG_4W_SCHEDULESC_D169759143_1736159709682.pdf"

    result = extract_text_from_pdf_via_svg_all_pages(PDF_PATH)
    text = result["full_text"]

    print("Total number of characters in document:", len(text))

    metadata = extract_insurance_metadata(text)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))



# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()
