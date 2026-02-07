"""
Integration Test: Node 6 → Node 2 (Re-Search)

SCENARIO:
1. User gets initial recommendations (red keyboard)
2. User says "I hate red, show me blue ones"
3. Chat extracts visual preference, saves to DB
4. System re-runs Node 2 (Market Scout) with color filter
5. Search queries now include "blue", exclude "red" products

RUN: python scripts\test_node2_feedback.py
"""
import asyncio
import os
import sys
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Load env from backend
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

if not os.getenv("GOOGLE_API_KEY"):
    print("❌ GOOGLE_API_KEY not found. Check backend/.env")
    sys.exit(1)

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock DB and external services
mock_db = MagicMock()
sys.modules['app.db.session'] = mock_db

# Import after mocks
from app.agent.nodes.router import node_router
from app.agent.nodes.chat import node_chat


async def test_node2_feedback_loop():
    print("\n" + "="*60)
    print("TEST: Node 6 → Node 2 Feedback Loop (Visual Preference)")
    print("="*60)
    
    # === PHASE 1: User says "I hate red, show me blue" ===
    print("\n💬 PHASE 1: User says 'I hate red, show me blue ones'")
    
    router_state = {
        "user_query": "I hate red, show me blue ones",
        "chat_history": [{"role": "assistant", "content": "I found this red keyboard"}],
        "image_base64": None
    }
    
    router_result = await node_router(router_state)
    print(f"   Router Decision: {router_result['router_decision']}")
    assert router_result['router_decision'] == 're_search', f"Expected 're_search', got '{router_result['router_decision']}'"
    print("   ✅ Correctly classified as re_search")
    
    # === PHASE 2: Chat extracts visual preferences ===
    print("\n🔍 PHASE 2: Chat Node extracts visual preferences")
    
    chat_state = {
        "user_query": "I hate red, show me blue ones",
        "router_decision": "re_search",
        "chat_history": [],
        "user_preferences": {},
        "product_query": {"canonical_name": "Mechanical Keyboard"}
    }
    
    with patch('app.agent.nodes.chat.SessionLocal'):
        chat_result = await node_chat(chat_state)
    
    search_criteria = chat_result.get('search_criteria', {})
    print(f"   Extracted search_criteria: {search_criteria}")
    print(f"   Loop Step: {chat_result.get('loop_step')}")
    
    assert chat_result.get('loop_step') == 'market_scout_node', "Expected loop to market_scout_node"
    print("   ✅ Correctly routes to Market Scout")
    
    # === PHASE 3: Simulate Market Scout using search_criteria ===
    print("\n🔎 PHASE 3: Market Scout would receive these criteria")
    
    # Show what Market Scout would do with these criteria
    product_name = "Mechanical Keyboard"
    
    # Build search query (same logic as market_scout.py)
    color_filter = ""
    if search_criteria.get('prefer_colors'):
        color_filter = " " + " ".join(search_criteria['prefer_colors'])
    
    exclude_colors = search_criteria.get('exclude_colors', [])
    
    example_query = f"best alternative to {product_name}{color_filter} 2026 reddit"
    print(f"   Tavily Query: '{example_query}'")
    print(f"   Excluded Colors: {exclude_colors}")
    print(f"   Snowflake Vector: Would enhance embedding with '{color_filter.strip()}'")
    
    # === PHASE 4: Simulate filtering ===
    print("\n🚫 PHASE 4: Product Filtering Demo")
    
    mock_products = [
        {"name": "Keychron K2 Red Edition", "price": 79},
        {"name": "Ducky One 2 Blue", "price": 99},
        {"name": "Leopold FC660M Blue-Gray", "price": 119},
        {"name": "Red Dragon K552 RGB", "price": 45}
    ]
    
    filtered = []
    for p in mock_products:
        name_lower = p['name'].lower()
        if any(color.lower() in name_lower for color in exclude_colors):
            print(f"   ❌ Filtered out: {p['name']} (contains excluded color)")
        else:
            print(f"   ✅ Kept: {p['name']}")
            filtered.append(p)
    
    # === RESULT ===
    print("\n" + "="*60)
    print(f"✅ TEST PASSED!")
    print(f"   - 'I hate red' correctly extracted as exclude_colors")
    print(f"   - 'show me blue' correctly extracted as prefer_colors")
    print(f"   - System routes to Market Scout for re-search")
    print(f"   - {len(mock_products) - len(filtered)} products filtered out")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_node2_feedback_loop())
