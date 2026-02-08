"""
Integration Test: Node 6 → Node 2 (Re-Search)

SCENARIO: "I prefer Nike" -> Trigger new search with brand filter
"""
import asyncio
import os
import sys
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Load env from backend if on host, otherwise assume env vars or .env in root
if os.path.exists(os.path.join(os.getcwd(), 'backend')):
    load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
else:
    load_dotenv()
    sys.path.append(os.getcwd())

if not os.getenv("GOOGLE_API_KEY"):
    print("❌ GOOGLE_API_KEY not found. Check env vars.")
    sys.exit(1)

# Mock DB
mock_db_module = MagicMock()
sys.modules['app.db.session'] = mock_db_module

# Import after mocks
from app.agent.nodes.router import node_router
from app.agent.nodes.chat import node_chat
from app.agent.nodes.market_scout import node_market_scout

async def test_scenario_brand_preference():
    print("\n" + "="*60)
    print("SCENARIO: 'I prefer Nike' (Brand Preference)")
    print("="*60)
    
    # Step 1: Router
    router_state = {"user_query": "I like Nike", "chat_history": [], "image_base64": None}
    router_result = await node_router(router_state)
    print(f"\n📡 Router Decision: {router_result['router_decision']}")
    assert router_result['router_decision'] == 're_search', "Expected re_search for brand preference"
    
    # Step 2: Chat extracts preference
    chat_state = {"user_query": "I like Nike", "router_decision": "re_search", "chat_history": [], "user_preferences": {}}
    with patch('app.agent.nodes.chat.SessionLocal'):
        chat_result = await node_chat(chat_state)
    
    search_criteria = chat_result.get('search_criteria', {})
    print(f"   Extracted criteria: {search_criteria}")
    assert "Nike" in search_criteria.get('prefer_brands', []), "Expected 'Nike' in prefer_brands"
    
    # Step 3: Market Scout uses criteria
    # We mock Tavily search to verify the query construction
    
    scout_state = {
        "product_query": {"canonical_name": "Generic Running Shoes"},
        "user_preferences": {},
        "search_criteria": search_criteria
    }
    
    # Patch the actual location where the function is defined/imported from
    with patch('app.sources.tavily_client.search_market_context') as mock_search:
        mock_search.return_value = [{"title": "Nike Air Zoom", "price": "$120", "url": "http://nike.com"}]
        
        # Run Scout
        result = node_market_scout(scout_state)
        
        # Verify calls
        if mock_search.call_count > 0:
            # Check all calls for the brand filter
            found_brand = False
            for call in mock_search.call_args_list:
                args, _ = call
                query_used = args[0]
                print(f"   Query: {query_used}")
                if "Nike" in query_used:
                    found_brand = True
            
            if found_brand:
                print("✅ PASSED: Query includes 'Nike' brand filter")
            else:
                print("❌ FAILED: Query missing brand preference")
        else:
            print("❌ FAILED: Search function was not called")

if __name__ == "__main__":
    asyncio.run(test_scenario_brand_preference())
