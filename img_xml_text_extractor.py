import fitz  # PyMuPDF
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone


# ======================================
# PDF → SVG (SINGLE PAGE)
# ======================================
def extract_pdf_page_as_svg(pdf_path: str, output_svg_path: str, page_num: int):
    doc = None
    try:
        doc = fitz.open(pdf_path)

        if page_num >= doc.page_count:
            raise ValueError(f"Page number {page_num} out of range")

        page = doc[page_num]

        svg_content = page.get_svg_image(
            matrix=fitz.Matrix(1, 1),
            text_as_path=0  # keep text selectable
        )

        with open(output_svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

    except Exception as e:
        raise RuntimeError(f"SVG extraction failed on page {page_num + 1}: {str(e)}")

    finally:
        if doc:
            doc.close()


# ======================================
# SVG → TEXT
# ======================================
def extract_text_from_svg(svg_path: str) -> str:
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()

        namespaces = {"svg": "http://www.w3.org/2000/svg"}
        extracted_lines = []

        for text_elem in root.findall(".//svg:text", namespaces):
            parts = []

            for tspan in text_elem.findall(".//svg:tspan", namespaces):
                if tspan.text:
                    parts.append(tspan.text.strip())

            if text_elem.text and not parts:
                parts.append(text_elem.text.strip())

            if parts:
                extracted_lines.append(" ".join(parts))

        return "\n".join(extracted_lines)

    except ET.ParseError:
        raise RuntimeError("Invalid SVG XML structure")

    except Exception as e:
        raise RuntimeError(f"SVG text extraction failed: {str(e)}")


# ======================================
# FULL PDF PIPELINE (ALL PAGES)
# ======================================
def extract_text_from_pdf_via_svg_all_pages(
    pdf_path: str,
    temp_dir: str = "temp_svg"
) -> dict:
    """
    SUCCESS RETURN:
    {
      "total_pages": int,
      "pages": {1: "text", 2: "text"},
      "full_text": "---- PAGE 1 ---- text ---- PAGE 2 ----",
      "created_at": ISO_DATETIME
    }

    ERROR RETURN:
    {
      "error": "message",
      "stage": "stage_name",
      "created_at": ISO_DATETIME
    }
    """

    try:
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError("PDF file not found")

        if pdf_path.stat().st_size == 0:
            raise ValueError("PDF file is empty")

        temp_dir = Path(temp_dir)
        temp_dir.mkdir(exist_ok=True)

        # Open once to get page count
        doc = fitz.open(pdf_path)
        page_count = doc.page_count
        doc.close()

        pages_text = {}
        full_text_parts = []

        for page_num in range(page_count):
            svg_path = temp_dir / f"page_{page_num + 1}.svg"

            extract_pdf_page_as_svg(
                pdf_path=str(pdf_path),
                output_svg_path=str(svg_path),
                page_num=page_num
            )

            page_text = extract_text_from_svg(str(svg_path))
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
            "stage": "extract_text_from_pdf_via_svg_all_pages",
            "created_at": datetime.now(timezone.utc).astimezone().isoformat()
        }


# ======================================
# Example Usage
# ======================================
# if __name__ == "__main__":
#     PDF_PATH = "../data/NivaBupa/35091132202500.pdf"

#     result = extract_text_from_pdf_via_svg_all_pages(PDF_PATH)

#     print(f"\nTotal Pages: {result['total_pages']}\n")

#     print("\n===== FULL TEXT (FOR REGEX) =====\n")
#     print(result["full_text"])
