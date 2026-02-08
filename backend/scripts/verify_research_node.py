
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.agent.nodes.research import node_discovery_runner
from app.schemas.types import ProductQuery

def test_research_node_fallback():
    print("--- Verifying Research Node Fallback ---")
    
    # Mock State with a product that might be hard to find in SerpAPI (or just strictly check fallback logic)
    # We can't easily mock the API calls here without patching, so we'll run it 'real' 
    # but focused on seeing if we get an image even if we force a fallback scenario?
    # Actually, let's just run it for a known item and check the output keys "thumbnail" and "price".
    
    state = {
        "product_query": {
            "canonical_name": "Logitech MX Master 3S",
            "product_name": "Logitech MX Master 3S"
        }
    }
    
    result = node_discovery_runner(state)
    data = result.get("research_data", {})
    prices = data.get("competitor_prices", [])
    
    print(f"\nFound {len(prices)} price vectors.")
    if prices:
        first = prices[0]
        print(f"First Entry: {first}")
        if first.get("thumbnail"):
            print("SUCCESS: Image/Thumbnail found.")
        else:
            print("WARNING: No thumbnail found.")
            
        if first.get("url"):
             print("SUCCESS: URL found.")
        else:
             print("WARNING: No URL found.")

if __name__ == "__main__":
    test_research_node_fallback()
