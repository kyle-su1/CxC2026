
import os
import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")

api_key = os.getenv("SERPAPI_API_KEY")
print(f"Checking SerpAPI Key: {api_key[:5]}...{api_key[-5:]}")

try:
    params = {
        "engine": "google_shopping",
        "q": "iphone 15 pro",
        "api_key": api_key,
        "num": 1
    }
    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
    data = resp.json()
    
    if "error" in data:
        print(f"❌ SerpAPI Error: {data['error']}")
    elif "shopping_results" in data:
        print(f"✅ SerpAPI Working! Found {len(data['shopping_results'])} results.")
    else:
        print(f"⚠️ Unknown response: {data.keys()}")

except Exception as e:
    print(f"❌ Exception: {e}")
