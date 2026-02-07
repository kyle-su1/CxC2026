"""
Quick test of SerpAPI Google Lens with a public image URL.
"""
import requests
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

# Public Keychron keyboard image
IMAGE_URL = "https://www.keychron.com/cdn/shop/products/Keychron-K8-Pro-QMK-VIA-wireless-mechanical-keyboard-for-Mac-Windows-Linux-rgb-backlight-with-hot-swappable-Gateron-G-Pro-mechanical-switch-brown.jpg"

def test_lens():
    api_key = settings.SERPAPI_API_KEY
    if not api_key:
        print("ERROR: SERPAPI_API_KEY not set")
        return
    
    params = {
        "engine": "google_lens",
        "url": IMAGE_URL,
        "api_key": api_key,
        "hl": "en",
        "country": "ca"
    }
    
    print(f"Testing SerpAPI Google Lens...")
    print(f"Image URL: {IMAGE_URL[:60]}...")
    
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=60)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Save full response
        with open("/app/serpapi_lens_test_results.json", "w") as f:
            json.dump(data, f, indent=2)
        print("Full response saved to /app/serpapi_lens_test_results.json")
        
        print(f"\nResponse keys: {list(data.keys())}")
        
        if "knowledge_graph" in data:
            kg = data["knowledge_graph"]
            print(f"\n=== Knowledge Graph ===")
            print(f"Title: {kg.get('title')}")
            print(f"Description: {kg.get('description')}")
        
        if "visual_matches" in data:
            print(f"\n=== Visual Matches ({len(data['visual_matches'])}) ===")
            for i, match in enumerate(data["visual_matches"][:5]):
                print(f"{i+1}. {match.get('title')}")
                print(f"   Source: {match.get('source')}")
        
        if "shopping_results" in data:
            print(f"\n=== Shopping Results ({len(data['shopping_results'])}) ===")
            for i, item in enumerate(data["shopping_results"][:3]):
                print(f"{i+1}. {item.get('title')}")
                print(f"   Price: {item.get('price')}")
    else:
        print(f"Error: {response.text[:500]}")

if __name__ == "__main__":
    test_lens()
