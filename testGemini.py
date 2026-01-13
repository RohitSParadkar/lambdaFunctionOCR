import requests, json, os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

resp = requests.post(
    f"{url}?key={GEMINI_API_KEY}",
    headers={"Content-Type": "application/json"},
    data=json.dumps({
        "contents": [{"parts": [{"text": "Say hello"}]}]
    })
)

print(resp.status_code)
print(resp.text)
