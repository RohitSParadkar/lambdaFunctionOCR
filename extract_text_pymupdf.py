import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime, timezone


# ======================================
# UTIL: GET PASSWORD FROM FILE NAME
# ======================================
def get_password_from_filename(pdf_path: Path) -> str | None:
    """
    Example:
    29054955_02091994.pdf -> password = 02091994
    """
    name = pdf_path.stem
    parts = name.split("_")
    return parts[-1] if len(parts) > 1 else None


# ======================================
# FULL PDF TEXT EXTRACTION (ALL PAGES)
# ======================================
def extract_text_full_pdf(pdf_path: str) -> dict:
    doc = None
    try:
        pdf_path = Path(pdf_path)

        # Validate file
        if not pdf_path.exists():
            raise FileNotFoundError("PDF file not found")

        if pdf_path.stat().st_size == 0:
            raise ValueError("PDF file is empty")

        # Open PDF
        doc = fitz.open(pdf_path)

        #Handle encrypted PDF
        if doc.is_encrypted:
            password = get_password_from_filename(pdf_path)
            if not password or not doc.authenticate(password):
                raise RuntimeError("Failed to decrypt PDF using filename password")

        page_count = doc.page_count
        pages_text = {}
        full_text_parts = []

        # Extract text page by page
        for page_num in range(page_count):
            page = doc[page_num]

            # This preserves proper spacing
            page_text = page.get_text("text")

            pages_text[page_num + 1] = page_text

            full_text_parts.append(f"\n--- PAGE {page_num + 1} ---\n")
            full_text_parts.append(page_text)

        return {
            "total_pages": page_count,
            "pages": pages_text,
            "full_text": "\n".join(full_text_parts),
            "created_at": datetime.now(timezone.utc).astimezone().isoformat()
        }

    except Exception as e:
        return {
            "error": str(e),
            "stage": "extract_text_from_pdf_all_pages",
            "created_at": datetime.now(timezone.utc).astimezone().isoformat()
        }

    finally:
        if doc:
            doc.close()

