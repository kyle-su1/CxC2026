"""Test cropping and Lens with full output."""
import sys
import json
sys.path.insert(0, '/app')

from app.services.image_crop import crop_to_bounding_box
from app.services.image_hosting import store_temp_image, get_public_image_url
from app.core.config import settings
import requests

# Test with keychron image
with open("/app/keychron.webp", "rb") as f:
    image_bytes = f.read()

print(f"Original image size: {len(image_bytes)} bytes")

# Use full image as test (largest bbox)
bbox = [0, 0, 1000, 1000]

# Crop the image
cropped = crop_to_bounding_box(image_bytes, bbox)
print(f"Cropped image size: {len(cropped)} bytes")

# Store and get URL
image_id = store_temp_image(cropped, "jpg")
url = get_public_image_url(image_id)
print(f"Public URL: {url}")
print(f"PUBLIC_BASE_URL: {settings.PUBLIC_BASE_URL}")

# Call Lens directly
params = {
    "engine": "google_lens",
    "url": url,
    "api_key": settings.SERPAPI_API_KEY,
    "hl": "en",
    "country": "ca"
}

print("\nCalling SerpAPI Lens...")
try:
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=60)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nKeys: {list(data.keys())}")
        
        if "visual_matches" in data:
            print(f"\nVisual matches ({len(data['visual_matches'])}):")
            for i, m in enumerate(data['visual_matches'][:5]):
                print(f"  {i+1}. {m.get('title')}")
        
        if "shopping_results" in data:
            print(f"\nShopping results ({len(data['shopping_results'])}):")
            for i, s in enumerate(data['shopping_results'][:3]):
                print(f"  {i+1}. {s.get('title')}")
        
        if "error" in data:
            print(f"\nError: {data['error']}")
    else:
        print(f"Error: {response.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")
