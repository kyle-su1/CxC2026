
import sys
import os

# Add parent dir to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.agent.nodes.analysis import node_analysis_synthesis
from app.agent.state import AgentState

def test_analysis_schema():
    print("--- Verifying Analysis Node JSON Schema ---")
    
    # Mock State
    state = {
        "market_scout_data": {
            "candidates": [
                {
                    "name": "Alternative 1",
                    "reason": "Cheaper",
                    "image_url": "http://img.com/1",
                    "purchase_link": "http://buy.com/1",
                    "price_text": "$99.00",
                    "prices": [{"price": 99.0}]
                }
            ]
        },
        "research_data": {
             "competitor_prices": [{"price": 120.0, "thumbnail": "http://main.img", "url": "http://main.link"}]
        },
        "product_query": {
            "canonical_name": "Main Product"
        },
        "user_preferences": {}
    }
    
    try:
        result = node_analysis_synthesis(state)
        analysis = result.get("analysis_object", {})
        
        # 1. Verify Active Product (Main Card)
        active = analysis.get("active_product", {})
        print(f"\n[Check] Active Product Keys: {list(active.keys())}")
        assert "image_url" in active, "Missing image_url in active_product"
        assert "purchase_link" in active, "Missing purchase_link in active_product"
        assert "price_text" in active, "Missing price_text in active_product"
        
        # 2. Verify Price Analysis (Verdict)
        price_analysis = analysis.get("price_analysis", {})
        print(f"[Check] Price Analysis: {price_analysis}")
        assert "verdict" in price_analysis, "Missing verdict"
        
        # 3. Verify Alternatives (Hybrid Keys)
        alts = analysis.get("alternatives", [])
        if alts:
            first_alt = alts[0]
            print(f"[Check] Alternative Keys: {list(first_alt.keys())}")
            assert "image" in first_alt, "Missing 'image' key for frontend"
            assert "link" in first_alt, "Missing 'link' key for frontend"
            
        print("\nSUCCESS: JSON Schema matches Frontend expectations.")
        
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analysis_schema()
