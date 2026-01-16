import os
import fitz  # PyMuPDF

pdf_path = "../passwordProtectedFiles/HDFC Life/29054955_02091994.pdf"

# Extract filename without extension
filename = os.path.splitext(os.path.basename(pdf_path))[0]

# Password = part after underscore
password = filename.split("_")[-1]

doc = fitz.open(pdf_path)

if doc.is_encrypted:
    if not doc.authenticate(password):
        raise ValueError(f"Incorrect password for {pdf_path}")

print("PDF opened successfully")

# Example: read first page text
text = doc[0].get_text()
print(text)
