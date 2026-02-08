import os
import sys
import asyncio
import json

# Add parent dir to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from app.agent.nodes.market_scout import node_market_scout

# Mock State
state = {
    "product_query": {"product_name": "Logitech MX Master 3S", "visual_attributes": "ergonomic mouse"},
    "user_preferences": {"price_sensitivity": 0.5},
    "search_criteria": {}
}

print("--- Testing Market Scout Node ---")
try:
    result = node_market_scout(state)
    
    scout_data = result.get("market_scout_data", {})
    candidates = scout_data.get("candidates", [])
    
    print(f"\nFound {len(candidates)} candidates:")
    for cand in candidates:
        print(f"\n[Candidate] {cand.get('name')}")
        print(f"  - Price: {cand.get('price_text')} (Val: {cand.get('estimated_price')})")
        print(f"  - Image: {cand.get('image_url')}")
        print(f"  - Link: {cand.get('purchase_link')}")
        print(f"  - Raw Prices: {len(cand.get('prices', []))}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
