import requests,os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# ZOHO CREDENTIALS
# =========================



CLIENT_ID = os.getenv("CLIENT_ID") 
CLIENT_SECRET = os.getenv("CLIENT_SECRET") 
AUTH_CODE = os.getenv("REFRESH_TOKEN") 
REDIRECT_URI = "http://localhost"

url = "https://accounts.zoho.in/oauth/v2/token"  # IN domain

payload = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "code": AUTH_CODE
}

response = requests.post(url, data=payload)
print(response.json())
