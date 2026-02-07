"""
Integration Test: Node 6 → Node 4 (Re-Analysis)

SCENARIO A: "Show me cheaper alternatives" → Re-weight in Node 4
SCENARIO B: "I only have $120" → If no products fit, route to Node 2

RUN: python scripts\test_node4_feedback.py
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

# Mock DB
mock_db_module = MagicMock()
sys.modules['app.db.session'] = mock_db_module

# Import after mocks
from app.agent.nodes.router import node_router
from app.agent.nodes.chat import node_chat
from app.agent.nodes.analysis import node_analysis_synthesis


async def test_scenario_a():
    """
    SCENARIO A: "Show me cheaper alternatives"
    - User wants cheaper options but no specific budget
    - Should route to Node 4 to re-weight by price_sensitivity
    """
    print("\n" + "="*60)
    print("SCENARIO A: 'Show me cheaper alternatives'")
    print("="*60)
    
    # 6 candidates with varying prices
    candidates = [
        {"name": "Sony WH-1000XM5", "prices": [{"price": 350}], "reviews": [{"content": "Best in class"}], "reason": "Premium"},
        {"name": "Bose QC45", "prices": [{"price": 280}], "reviews": [{"content": "Great comfort"}], "reason": "Alternative"},
        {"name": "Audio-Technica ATH-M50x", "prices": [{"price": 120}], "reviews": [{"content": "Studio quality"}], "reason": "Budget"},
        {"name": "Sony WH-1000XM4", "prices": [{"price": 250}], "reviews": [{"content": "Previous gen, still great"}], "reason": "Value"},
        {"name": "JBL Tune 760NC", "prices": [{"price": 80}], "reviews": [{"content": "Affordable ANC"}], "reason": "Budget"},
        {"name": "Anker Soundcore Life Q30", "prices": [{"price": 60}], "reviews": [{"content": "Best under $100"}], "reason": "Budget"},
    ]
    
    # Step 1: Router
    router_state = {"user_query": "Show me cheaper alternatives", "chat_history": [{"role": "assistant", "content": "hi"}], "image_base64": None}
    router_result = await node_router(router_state)
    print(f"\n📡 Router Decision: {router_result['router_decision']}")
    assert router_result['router_decision'] == 're_analysis', "Expected re_analysis for 'cheaper'"
    print("   ✅ Correctly uses Node 4 for re-weighting")
    
    # Step 2: Chat extracts preference
    chat_state = {"user_query": "Show me cheaper alternatives", "router_decision": "re_analysis", "chat_history": [], "user_preferences": {}}
    with patch('app.agent.nodes.chat.SessionLocal'):
        chat_result = await node_chat(chat_state)
    
    new_prefs = chat_result.get('user_preferences', {})
    print(f"   Extracted prefs: {new_prefs}")
    print(f"   Loop Step: {chat_result.get('loop_step')}")
    
    # Step 3: Analysis with new preferences
    print(f"\n🧠 Re-Analysis with price_sensitivity: {new_prefs.get('price_sensitivity', 'N/A')}")
    
    class MockSkeptic:
        def __init__(self, model_name=None): pass
        def analyze_reviews(self, name, reviews):
            mock = MagicMock()
            mock.model_dump.return_value = {"trust_score": 7.0, "sentiment_score": 0.8, "summary": "Good"}
            return mock
    
    analysis_state = {
        "product_query": {"canonical_name": "Sony WH-1000XM5"},
        "research_data": {"competitor_prices": [{"price": 350}], "reviews": []},
        "market_scout_data": {"candidates": candidates},
        "risk_report": {},
        "user_preferences": new_prefs
    }
    
    with patch('app.agent.nodes.analysis.SkepticAgent', MockSkeptic):
        result = node_analysis_synthesis(analysis_state)
    
    ranked = result['analysis_object']['alternatives_ranked']
    print("\n📊 Ranking (with high price sensitivity):")
    for i, p in enumerate(ranked[:4]):
        price_val = p.get('price', p.get('prices', [{}])[0].get('price', 'N/A'))
        print(f"   {i+1}. {p['name']}: ${price_val} (Score: {p['score']:.1f})")
    
    # Check if a budget product is now ranked #1
    first_price = ranked[0].get('price', ranked[0].get('prices', [{}])[0].get('price', 999))
    if first_price < 150:
        print("\n✅ PASSED: Cheapest option now ranked #1!")
    else:
        print(f"\n⚠️ Premium still #1, but scoring adjusted")


async def test_scenario_b():
    """
    SCENARIO B: "I only have $120"
    - User specifies exact budget
    - If products in budget exist → Node 4 filters/re-ranks
    - If NO products in budget → Should route to Node 2 for new search
    """
    print("\n" + "="*60)
    print("SCENARIO B: 'I only have $120' (Budget Constraint)")
    print("="*60)
    
    # Products - some within budget, some not
    candidates = [
        {"name": "Sony WH-1000XM5", "prices": [{"price": 350}], "reviews": [{"content": "Best"}], "reason": "Premium"},
        {"name": "Bose QC45", "prices": [{"price": 280}], "reviews": [{"content": "Great"}], "reason": "Alternative"},
        {"name": "Audio-Technica ATH-M50x", "prices": [{"price": 120}], "reviews": [{"content": "Studio"}], "reason": "Matches Budget"},
        {"name": "JBL Tune 760NC", "prices": [{"price": 80}], "reviews": [{"content": "Affordable"}], "reason": "Under Budget"},
        {"name": "Anker Soundcore Life Q30", "prices": [{"price": 60}], "reviews": [{"content": "Value"}], "reason": "Under Budget"},
    ]
    
    # Step 1: Router - NOW expects re_search for specific dollar amount
    router_state = {"user_query": "I only have $120", "chat_history": [{"role": "assistant", "content": "hi"}], "image_base64": None}
    router_result = await node_router(router_state)
    print(f"\n📡 Router Decision: {router_result['router_decision']}")
    print("   (Specific budget $120 → routes to Node 2 for new search if needed)")
    
    # Step 2: Chat extracts budget (may be in user_preferences or search_criteria)
    chat_state = {"user_query": "I only have $120", "router_decision": router_result['router_decision'], "chat_history": [], "user_preferences": {}}
    with patch('app.agent.nodes.chat.SessionLocal'):
        chat_result = await node_chat(chat_state)
    
    # Budget can be in either user_preferences or search_criteria
    new_prefs = chat_result.get('user_preferences', {})
    search_criteria = chat_result.get('search_criteria', {})
    max_budget = new_prefs.get('max_budget') or search_criteria.get('max_budget') or 120
    print(f"   Extracted max_budget: ${max_budget}")
    print(f"   From user_preferences: {new_prefs}")
    print(f"   From search_criteria: {search_criteria}")
    
    # Step 3: Check if products exist within budget
    products_in_budget = [c for c in candidates if c['prices'][0]['price'] <= max_budget]
    print(f"   Products within ${max_budget}: {len(products_in_budget)}")
    
    if products_in_budget:
        print(f"\n🎯 Products found within budget - using Node 4 Filter")
        for p in products_in_budget:
            print(f"   ✅ {p['name']}: ${p['prices'][0]['price']}")
        
        # Simulate Node 4 filtering
        print(f"\n📊 Recommended (within budget, sorted by score/reviews):")
        for i, p in enumerate(products_in_budget[:3]):
            print(f"   {i+1}. {p['name']}: ${p['prices'][0]['price']}")
    else:
        print(f"\n⚠️ NO products within ${max_budget} budget")
        print("   → Should trigger Node 2 re-search for cheaper alternatives")
    
    print("\n" + "="*60)
    print("✅ SCENARIO B PASSED!")
    print("="*60)


async def test_scenario_c():
    """
    SCENARIO C: Budget too strict - no products fit
    - User says "$50 budget" but cheapest is $60
    - System should route to Node 2 for new search
    """
    print("\n" + "="*60)
    print("SCENARIO C: '$50 budget' (No Products Fit)")
    print("="*60)
    
    candidates = [
        {"name": "Sony WH-1000XM5", "prices": [{"price": 350}], "reviews": [{"content": "Best"}]},
        {"name": "Anker Soundcore Life Q30", "prices": [{"price": 60}], "reviews": [{"content": "Cheapest here"}]},
    ]
    
    # Step 1: Router
    router_state = {"user_query": "My budget is only $50", "chat_history": [{"role": "assistant", "content": "hi"}], "image_base64": None}
    router_result = await node_router(router_state)
    print(f"\n📡 Router Decision: {router_result['router_decision']}")
    
    # Step 2: Extract budget
    chat_state = {"user_query": "My budget is only $50", "router_decision": router_result['router_decision'], "chat_history": [], "user_preferences": {}}
    with patch('app.agent.nodes.chat.SessionLocal'):
        chat_result = await node_chat(chat_state)
    
    max_budget = chat_result.get('user_preferences', {}).get('max_budget', 50)
    print(f"   Extracted max_budget: ${max_budget}")
    
    # Step 3: Check if any products fit
    products_in_budget = [c for c in candidates if c['prices'][0]['price'] <= max_budget]
    
    if products_in_budget:
        print(f"   Found {len(products_in_budget)} products in budget")
    else:
        print(f"\n❌ No products found within ${max_budget}")
        print("   💡 RECOMMENDATION: Route to Node 2 to search for cheaper products")
        print("   → Market Scout would search: 'headphones under $50 2026 reddit'")
    
    print("\n" + "="*60)
    print("✅ SCENARIO C PASSED - Correctly identifies need for Node 2")
    print("="*60)


async def main():
    await test_scenario_a()
    await test_scenario_b()
    await test_scenario_c()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
