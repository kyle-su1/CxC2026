import asyncio
import os
import sys
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock DB
sys.modules['app.db.session'] = MagicMock()

# Import after mocks
from app.agent.nodes.analysis import node_analysis_synthesis
from app.agent.nodes.response import node_response_formulation
from app.agent.state import AgentState

# Mock Skeptic Agent to ensure consistent sentiment scores
# This isolates the effect of Price Sensitivity
class MockSkepticAgent:
    def __init__(self, model_name=None):
        pass
    
    def analyze_reviews(self, product_name, reviews):
        # Return a fixed high sentiment score for simplicity
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "trust_score": 5.0,
            "sentiment_score": 0.9, # High quality
            "summary": "Excellent product with great features."
        }
        return mock_result

async def run_test():
    print("\n=== TEST: Effect of 'Cheaper Alternatives' Preference ===\n")

    # Define two products: one expensive, one cheap
    # Current Market Average calculation in Node 4 requires multiple products
    candidates = [
        {
            "name": "Luxury Pro Model",
            "prices": [{"price": 200.0}],
            "reviews": [{"content": "Amazing but pricey"}],
            "reason": "Original Selection"
        },
        {
            "name": "Budget Friendly Option",
            "prices": [{"price": 50.0}],
            "reviews": [{"content": "Good value"}],
            "reason": "Visual Match"
        }
    ]

    base_state = {
        "research_data": {
            "product_query": {"canonical_name": "Luxury Pro Model"},
            "competitor_prices": [{"price": 200.0}],
            "reviews": []
        },
        "market_scout_data": {"candidates": candidates},
        "risk_report": {},
        "user_preferences": {}
    }

    # Patch SkepticAgent
    with patch('app.agent.nodes.analysis.SkepticAgent', side_effect=MockSkepticAgent):
        
        # --- SCENARIO 1: No Price Sensitivity (Rich User) ---
        print("--- Scenario 1: Low Price Sensitivity (0.1) ---")
        state_1 = base_state.copy()
        state_1["user_preferences"] = {"price_sensitivity": 0.1, "quality": 0.9}
        
        result_1 = node_analysis_synthesis(state_1)
        # FIX: 'alternatives_ranked' has 'score', not 'score_details'
        res1_scores = {p['name']: p['score'] for p in result_1['analysis_object']['alternatives_ranked']}
        print(f"Scores (Low Sensitivity): {res1_scores}")
        
        # --- SCENARIO 2: High Price Sensitivity (Budget User) ---
        print("\n--- Scenario 2: High Price Sensitivity (0.9) ---")
        state_2 = base_state.copy()
        state_2["user_preferences"] = {"price_sensitivity": 0.9, "quality": 0.5}
        
        result_2 = node_analysis_synthesis(state_2)
        # FIX: 'alternatives_ranked' has 'score', not 'score_details'
        res2_scores = {p['name']: p['score'] for p in result_2['analysis_object']['alternatives_ranked']}
        print(f"Scores (High Sensitivity): {res2_scores}")

        # Check Delta
        val_lux_1 = res1_scores.get("Luxury Pro Model", 0)
        val_lux_2 = res2_scores.get("Luxury Pro Model", 0)
        val_bud_1 = res1_scores.get("Budget Friendly Option", 0)
        val_bud_2 = res2_scores.get("Budget Friendly Option", 0)
        
        diff_lux = val_lux_2 - val_lux_1
        diff_bud = val_bud_2 - val_bud_1
        
        print("\n--- Impact Analysis ---")
        print(f"Luxury Score Change: {diff_lux:.2f}")
        print(f"Budget Score Change: {diff_bud:.2f}")
        
        if val_bud_2 > val_lux_2:
             print("✅ RESULT: Budget option WON in Scenario 2!")
        else:
             print("⚠️ RESULT: Luxury option still won (adjust weights or logic if this is unexpected).")

        # --- Generate Response for Scenario 2 ---
        print("\n--- Generating Node 5 Response for Scenario 2 (Budget User) ---")
        # We need to merge the analysis result into the state
        state_2_final = state_2.copy()
        state_2_final.update(result_2)
        
        # We allow real LLM call here to see the text
        try:
            response_result = node_response_formulation(state_2_final)
            print("\nFinal Response Verdict:")
            print(response_result['final_recommendation'].get('verdict'))
            print("\nAlternatives Summary:")
            for alt in response_result['final_recommendation'].get('alternatives', []):
                 print(f"- {alt['name']}: {alt.get('summary')}")
                 
        except Exception as e:
            print(f"Response Node Failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_test())
