"""
Complete test of SerpAPI Google Lens with self-hosted images via ngrok.

USAGE:
1. Start ngrok: ngrok http 8000
2. Set PUBLIC_BASE_URL in backend/.env to your ngrok URL
3. Restart backend: docker-compose restart backend
4. Run: docker-compose exec backend python scripts/test_hybrid_lens.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from app.core.config import settings
from app.services.image_hosting import store_temp_image, get_public_image_url


def test_hybrid_lens(image_path: str):
    """
    Full test: store image → get public URL → call SerpAPI Lens.
    """
    print(f"\n=== Hybrid Vision Pipeline Test ===")
    print(f"Image: {image_path}")
    print(f"PUBLIC_BASE_URL: {settings.PUBLIC_BASE_URL}")
    
    if "localhost" in settings.PUBLIC_BASE_URL:
        print("\n⚠️  WARNING: PUBLIC_BASE_URL is localhost!")
        print("   SerpAPI cannot access localhost. Set PUBLIC_BASE_URL to your ngrok URL.")
        print("   Example: export PUBLIC_BASE_URL=https://abcd1234.ngrok.io")
        return {"error": "PUBLIC_BASE_URL must be a public URL (e.g., ngrok)"}
    
    # Step 1: Read and store the image
    print("\n[Step 1] Storing image temporarily...")
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    extension = image_path.split(".")[-1].lower()
    image_id = store_temp_image(image_bytes, extension)
    print(f"   Image ID: {image_id}")
    
    # Step 2: Get public URL
    print("\n[Step 2] Getting public URL...")
    public_url = get_public_image_url(image_id)
    print(f"   URL: {public_url}")
    
    # Step 3: Call SerpAPI Lens
    print("\n[Step 3] Calling SerpAPI Google Lens...")
    api_key = settings.SERPAPI_API_KEY
    if not api_key:
        return {"error": "SERPAPI_API_KEY not set"}
    
    params = {
        "engine": "google_lens",
        "url": public_url,
        "api_key": api_key,
        "hl": "en",
        "country": "ca"
    }
    
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=60)
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        return {"error": f"HTTP {response.status_code}: {response.text[:300]}"}
    
    results = response.json()
    
    # Save full response
    with open("/app/serpapi_hybrid_test.json", "w") as f:
        json.dump(results, f, indent=2)
    print("   Full results saved to /app/serpapi_hybrid_test.json")
    
    # Step 4: Extract product information
    print("\n[Step 4] Extracting product information...")
    
    if "error" in results:
        print(f"   API Error: {results['error']}")
        return {"error": results["error"]}
    
    product_name = None
    
    # Try knowledge_graph first
    if "knowledge_graph" in results:
        kg = results["knowledge_graph"]
        product_name = kg.get("title")
        print(f"   Knowledge Graph: {product_name}")
    
    # Try visual_matches
    if "visual_matches" in results:
        print(f"   Visual Matches ({len(results['visual_matches'])}):")
        for i, match in enumerate(results["visual_matches"][:5]):
            print(f"      {i+1}. {match.get('title')}")
            if not product_name:
                product_name = match.get("title")
    
    # Try shopping_results
    if "shopping_results" in results:
        print(f"   Shopping Results ({len(results['shopping_results'])}):")
        for i, item in enumerate(results["shopping_results"][:3]):
            print(f"      {i+1}. {item.get('title')} - {item.get('price')}")
    
    print(f"\n=== RESULT ===")
    print(f"Identified Product: {product_name or 'Unknown'}")
    
    return {
        "product_name": product_name,
        "image_url": public_url,
        "visual_matches": len(results.get("visual_matches", [])),
        "shopping_results": len(results.get("shopping_results", []))
    }


if __name__ == "__main__":
    test_image = "/app/keychron.webp"
    
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    
    if not os.path.exists(test_image):
        print(f"Image not found: {test_image}")
        sys.exit(1)
    
    result = test_hybrid_lens(test_image)
    print(f"\nFinal: {json.dumps(result, indent=2)}")
