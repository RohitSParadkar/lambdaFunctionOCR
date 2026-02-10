import pdfplumber
import re
import json
from pathlib import Path
from PyPDF2 import PdfReader



# ---------- TEXT NORMALIZATION ----------
def normalize_text(text: str) -> str:
    """
    Cleans PDF text so regex works reliably
    """
    if not text:
        return ""

    text = text.replace("\xa0", " ")                # non-breaking space
    text = re.sub(r"[ \t]+", " ", text)             # extra spaces
    text = re.sub(r"\n+", "\n", text)               # multiple newlines
    text = re.sub(r"\n\s+", "\n", text)             # newline + spaces
    return text.strip()


# ---------- PDF EXTRACTION ----------
def extract_pdf(file_path: str):
    full_text = ""
    pages_data = []

    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            clean_page_text = normalize_text(page_text)

            pages_data.append({
                "page_number": i,
                "text": clean_page_text
            })

            full_text += clean_page_text + "\n"

    return normalize_text(full_text), pages_data


# ---------- SAVE FILES ----------
def save_outputs(text, pages_data, output_dir="output"):
    Path(output_dir).mkdir(exist_ok=True)

    # Save clean TXT
    with open(f"{output_dir}/policy_clean.txt", "w", encoding="utf-8") as f:
        f.write(text)

    # Save JSON (page-wise)
    with open(f"{output_dir}/policy_pages.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "document_type": "Motor Insurance Policy",
                "source": "PDF",
                "pages": pages_data
            },
            f,
            indent=2,
            ensure_ascii=False
        )

def resolve_data_path(input_path: str) -> Path:
    """
    Convert paths like '../data/xxx.pdf' to absolute project data paths
    """
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "data"

    path = Path(input_path)

    # Strip everything up to and including 'data'
    if "data" in path.parts:
        relative_path = Path(*path.parts[path.parts.index("data") + 1:])
    else:
        relative_path = path.name

    return data_dir / relative_path

def save_full_text_to_file(full_text: str,output_dir="temp_text"):
    """
    Saves full_text to a fixed temp file.
    Overwrites the same file on every run.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
   
    txt_path = output_dir / f"full_text.txt"

    # 'w' mode ALWAYS overwrites the file
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    return str(txt_path)


# ======================================
# TEXT → MARKDOWN FILE
# ======================================
def save_extracted_text_as_markdown(
    extraction_result: dict,
    output_md_path: str
):
    """
    Converts extracted PDF text into a Markdown file.
    """

    if "error" in extraction_result:
        raise RuntimeError(f"Cannot create markdown: {extraction_result['error']}")

    lines = []

    # ---- Metadata ----
    lines.append("# 📄 PDF Extracted Text\n")
    lines.append(f"- **Total Pages:** {extraction_result['total_pages']}")
    lines.append(f"- **Created At:** {extraction_result['created_at']}")
    lines.append("\n---\n")

    # ---- Page-wise Content ----
    for page_num, page_text in extraction_result["pages"].items():
        lines.append(f"## Page {page_num}\n")

        if page_text.strip():
            lines.append(page_text)
        else:
            lines.append("_No text found on this page._")

        lines.append("\n---\n")

    # ---- Write Markdown File ----
    output_md_path = Path(output_md_path)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
