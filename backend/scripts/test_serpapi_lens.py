"""
SerpAPI Google Lens Product Identification Test Script
Uploads image to ImgBB (free hosting), then uses public URL with SerpAPI Lens.
"""
import os
import sys
import requests
import json
import base64

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

IMGBB_API_KEY = "5e9c51b6c4e6b0b0b0c0c0c0c0c0c0c0"  # Free API key for basic uploads

def upload_to_imgbb(image_path: str):
    """
    Uploads an image to ImgBB and returns the public URL.
    """
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={
                "key": IMGBB_API_KEY,
                "image": image_data,
                "name": os.path.basename(image_path)
            },
            timeout=30
        )
        
        result = response.json()
        if result.get("success"):
            url = result["data"]["url"]
            print(f"Image uploaded to: {url}")
            return url
        else:
            print(f"ImgBB upload failed: {result}")
            return None
    except Exception as e:
        print(f"ImgBB upload error: {e}")
        return None


def identify_product_from_url(image_url: str) -> dict:
    """
    Uses SerpAPI Google Lens with a public image URL to identify products.
    """
    api_key = settings.SERPAPI_API_KEY
    if not api_key:
        print("ERROR: SERPAPI_API_KEY not set in .env")
        return {"error": "Missing API key"}
    
    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": api_key,
        "hl": "en",
        "country": "ca"
    }
    
    print(f"Calling SerpAPI Google Lens with URL: {image_url[:60]}...")
    
    try:
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=60)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text[:500]}"}
        
        results = response.json()
        
        # Save full response for debugging
        with open("/app/serpapi_lens_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("Full results saved to /app/serpapi_lens_test_results.json")
        
        # Extract product information
        product_matches = []
        
        # Check for knowledge_graph (identified entity)
        if "knowledge_graph" in results:
            kg = results["knowledge_graph"]
            product_matches.append({
                "title": kg.get("title"),
                "description": kg.get("description"),
                "type": "knowledge_graph"
            })
        
        # Check for visual_matches (general visual similarity)
        if "visual_matches" in results:
            for match in results["visual_matches"][:5]:
                product_matches.append({
                    "title": match.get("title"),
                    "source": match.get("source"),
                    "link": match.get("link"),
                    "type": "visual_match"
                })
        
        # Check for shopping_results (direct product matches)
        if "shopping_results" in results:
            for item in results["shopping_results"][:3]:
                product_matches.append({
                    "title": item.get("title"),
                    "price": item.get("price"),
                    "source": item.get("source"),
                    "link": item.get("link"),
                    "type": "shopping_result"
                })
        
        print(f"\n=== IDENTIFIED PRODUCTS ===")
        for i, match in enumerate(product_matches[:8]):
            print(f"{i+1}. [{match.get('type')}] {match.get('title')}")
            if match.get('price'):
                print(f"   Price: {match.get('price')}")
            if match.get('source'):
                print(f"   Source: {match.get('source')}")
        
        return {
            "product_matches": product_matches,
            "best_guess": product_matches[0]["title"] if product_matches else "Unknown"
        }
        
    except Exception as e:
        return {"error": str(e)}


def identify_product_from_image(image_path: str) -> dict:
    """
    Main entry point: uploads image to ImgBB, then calls SerpAPI Lens.
    """
    print(f"\n=== SerpAPI Google Lens Product Identification ===")
    print(f"Image: {image_path}")
    
    # Step 1: Upload to ImgBB
    print("\n[Step 1] Uploading to ImgBB for public URL...")
    public_url = upload_to_imgbb(image_path)
    
    if not public_url:
        return {"error": "Failed to upload image to ImgBB"}
    
    # Step 2: Call SerpAPI with the URL
    print("\n[Step 2] Calling SerpAPI Google Lens...")
    return identify_product_from_url(public_url)


if __name__ == "__main__":
    test_image = "/app/keychron.webp"
    
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    
    if not os.path.exists(test_image):
        print(f"Test image not found at: {test_image}")
        print("Please provide an image path as argument:")
        print("  python test_serpapi_lens.py /path/to/image.jpg")
        sys.exit(1)
    
    result = identify_product_from_image(test_image)
    print(f"\n=== FINAL RESULT ===")
    print(json.dumps(result, indent=2))
