import pdfplumber



def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text(x_tolerance=2, y_tolerance=2) or ""
    return text

path = "./Folder_Structure/Process_Files/Automatic_Preprocess/Digital POSP/OG-25-1907-1802-00003058_Bajaj Allianz_Jyoti Kasurde_010425.pdf"
data = extract_text_from_pdf(path)
print("extractedData",data)