# Meta Data Extractor

This project extracts structured insurance policy metadata (such as product type, insurer name, policy dates, etc.) from insurance policy PDF documents using Google Gemini API.


## Project Structure
project-root/<br>
├── data/<br>
│ └── motorData/<br>
│ └── TATA_AIG/<br>
│ └── version2/<br>
│ └── Tata AIG Motor Policy Schedule_3188_6301931391-01.pdf<br>
├── img_xml_text_extractor.py<br>
├── extractor.py<br>
├── main.py<br>
├── .env<br>
├── requirements.txt<br>
└── README.md <br>

## Prerequisites

- Python 3.12 or higher
- pip
- Google Gemini API Key
- Virtual environment support (venv)

### Create Virtual Environment
Windows: <br>
python -m venv venv
Linux/macOS:<br>
python3 -m venv venv

### Activate Virtual Environment
Windows: <br>
venv\Scripts\activate

Linux / macOS:<br>
source venv/bin/activate

## Install Dependencies
pip install -r requirements.txt

## Configure Environment Variables
- Create a .env file in the project root.
- GEMINI_API_KEY=your_google_gemini_api_key_here

## Run the Application
### Configure PDF File Path (PDF_PATH)
The application processes a local PDF file.
You must update the PDF_PATH variable inside main.py to point to your local PDF file.Then from the project root directory run following command from Windows (PowerShell) or Linux terminal:<br>

Windows: <br>
python main.py

Linux / macOS:<br>
python3 main.py


## Sample Output Schema:
{
  "Policy_Number": "",
  "Insured_Name": "",
  "Insured_Contact_No": "",
  "Insurance_Company_Name": "",
  "Products": "",
  "Policy_Start_Date": "",
  "Policy_Expiry_Date": "",
  "Sum_Assured_OR_IDV": "",
  "Net_Premium": "",
  "Vehicle_Registration_No": "",
  "Business_Or_Retention_Type": "",
  "Created_At": ""
}
 
