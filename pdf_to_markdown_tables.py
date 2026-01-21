import pdfplumber
from pathlib import Path
from datetime import datetime, timezone


# ===============================
# HELPERS
# ===============================
def clean_cell(cell):
    return "" if cell is None else str(cell).strip()


def normalize_table(table):
    """
    Fixes pdfplumber tables:
    - None values
    - Key:Value rows
    """
    rows = []

    for row in table:
        row = [clean_cell(c) for c in row]

        # key:value inside single column
        if len(row) == 1 and ":" in row[0]:
            k, v = row[0].split(":", 1)
            rows.append([k.strip(), v.strip()])
            continue

        if any(row):
            rows.append(row)

    return rows


def table_to_markdown(table):
    if len(table) < 2:
        return None

    cols = max(len(r) for r in table)
    table = [r + [""] * (cols - len(r)) for r in table]

    md = []
    md.append("| " + " | ".join(table[0]) + " |")
    md.append("| " + " | ".join(["---"] * cols) + " |")

    for row in table[1:]:
        md.append("| " + " | ".join(row) + " |")

    return "\n".join(md)


# ===============================
# MAIN PDF → MARKDOWN
# ===============================
def pdf_to_markdown_full(pdf_path: str, output_md: str):
    pdf_path = Path(pdf_path)
    md = []

    md.append("# PDF Extracted Content\n")
    md.append(f"**File:** `{pdf_path.name}`  ")
    md.append(f"**Extracted At:** {datetime.now(timezone.utc).astimezone().isoformat()}\n")
    md.append("---\n")

    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            md.append(f"## Page {page_no}\n")

            # ---------- TEXT ----------
            text = page.extract_text()
            if text:
                md.append("### Text\n")
                md.append(text.strip())
                md.append("")

            # ---------- TABLES ----------
            tables = page.extract_tables()
            if tables:
                md.append("### Tables\n")

                for idx, raw_table in enumerate(tables, start=1):
                    clean = normalize_table(raw_table)
                    table_md = table_to_markdown(clean)

                    if table_md:
                        md.append(f"**Table {idx}**\n")
                        md.append(table_md)
                        md.append("")

            md.append("\n---\n")

    Path(output_md).write_text("\n".join(md), encoding="utf-8")


# ===============================
# RUN
# ===============================
# if __name__ == "__main__":
#     pdf_to_markdown_full(
#         pdf_path="./Folder_Structure/Unprocess_Files/SP_DG_4WAG_SCHEDULEHC_D225472786_D225472786_1758191608260.pdf",
#         output_md="output.md"
#     )
