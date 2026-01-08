import os
import json
from insertData import insert_json
from gemini_extractor import extract_insurance_metadata 
from img_xml_text_extractor import extract_text_from_pdf_via_svg_all_pages
# ==============================
# CONFIG
# ==============================
PDF_FOLDER_PATH = "./data/Policy Copy FY 25-26/POSP/Tata AIG/"   # folder containing PDFs

# FUNCTION: Process single PDF
# ==============================
def process_single_pdf(pdf_path: str) -> dict:
    """
    Extract text from a single PDF and return structured insurance metadata
    """
    try:
        # Step 1: Extract text from PDF
        pdf_result = extract_text_from_pdf_via_svg_all_pages(pdf_path)

        # Step 2: Get extracted text
        text = pdf_result.get("full_text", "")

        if not text:
            raise ValueError("No text extracted from PDF")

        # Step 3: Extract insurance metadata using Gemini
        result = extract_insurance_metadata(text)

        # Step 4: Add source file info
        result["source_file"] = os.path.basename(pdf_path)

        return result

    except Exception as e:
        return {
            "source_file": os.path.basename(pdf_path),
            "error": str(e)
        }


# FUNCTION: Process all PDFs in folder
def process_pdf_folder(folder_path: str):
    """
    Iterate through all PDF files in a folder, extract metadata,
    print JSON output, and insert into DB
    """
    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder_path, file_name)

            print(f"\n Processing: {file_name}")

            result = process_single_pdf(pdf_path)

            # JSON-only output
            print(json.dumps(result, ensure_ascii=False, indent=2))

            # insert into DB
            insert_json(result)



# MAIN

def main():
    process_pdf_folder(PDF_FOLDER_PATH)


# RUN
if __name__ == "__main__":
    main()
