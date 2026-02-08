import requests
import time
import base64
import json

BASE_URL = "http://localhost:8000/api/v1"

def wait_for_health():
    print("Waiting for backend to be healthy...")
    for i in range(30):
        try:
            # Health check is at root /health, not /api/v1/health
            response = requests.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("Backend is up!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    print("Timeout waiting for backend.")
    return False

def test_market_scout():
    print("Testing Market Scout (skipping vision)...")
    
    # Tiny 1x1 white pixel base64
    dummy_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNiAAAABgDNjd8qAAAAAElFTkSuQmCC"
    
    payload = {
        "image": dummy_image,
        "user_preferences": {"price_sensitivity": 0.5, "quality": 0.8},
        "user_query": "Find me a cheap alternative to iPhone 14",
        "detect_only": False,
        "skip_vision": True,
        "product_name": "iPhone 14"
    }
    
    try:
        # Endpoint is at /analyze, not /api/v1/analyze
        response = requests.post("http://localhost:8000/analyze", json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response Data Keys:", data.keys())
            if "market_scout_data" in str(data) or "candidates" in str(data):
                print("SUCCESS: Market Scout returned data.")
                return True
            if "error" in data:
                 print(f"API Returned Error: {data['error']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")
        return False
        
    return False

if __name__ == "__main__":
    if wait_for_health():
        if test_market_scout():
            print("\nVerification PASSED")
        else:
            print("\nVerification FAILED")
    else:
        print("\nBackend did not start.")
