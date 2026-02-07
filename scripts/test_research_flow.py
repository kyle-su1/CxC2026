import sys
import os
import json

# Ensure backend is in python path
sys.path.append(os.path.abspath("backend"))

from app.agent.nodes.vision import node_user_intent_vision
from app.agent.nodes.research import node_discovery_runner
from app.core.config import settings

def test_flow():
    print("=== Testing Flow: Vision (Node 1) -> Research (Node 2) ===\n")

    # 1. Initialize Dummy State (Image is irrelevant since Vision is mocked)
    initial_state = {
        "image_base64": "dummy_image_data",
        "user_query": "Is this a good deal?",
        "user_preferences": {}
    }

    # 2. Run Node 1: Vision (Mock)
    print(f"--- Running Node 1 (Vision) ---")
    vision_output = node_user_intent_vision(initial_state)
    print(f"OUTPUT: {json.dumps(vision_output, indent=2)}\n")

    # 3. Update State
    state_after_vision = {**initial_state, **vision_output}

    # 4. Run Node 2: Research (Real APIs)
    print(f"--- Running Node 2 (Research) with Real APIs ---")
    if "your_" in settings.TAVILY_API_KEY or "your_" in settings.SERPAPI_API_KEY:
         print("⚠️  WARNING: API Keys look like placeholders in .env. This might fail or return errors.")

    research_output = node_discovery_runner(state_after_vision)
    
    # 5. Display Results
    print(f"\nOUTPUT: Research Data Summary")
    data = research_output.get("research_data", {})
    
    print(f"Reviews Found: {len(data.get('reviews', []))}")
    for r in data.get('reviews', []):
        print(f" - [{r.get('source', 'Unknown')}] {r.get('url')}")
        
    print(f"\nPrices Found: {len(data.get('competitor_prices', []))}")
    for p in data.get('competitor_prices', []):
        print(f" - {p.get('vendor')}: ${p.get('price_cents', 0)/100} {p.get('currency', 'CAD')}")

    print(f"\nTrace: {json.dumps(data.get('trace', []), indent=2)}")

if __name__ == "__main__":
    test_flow()
