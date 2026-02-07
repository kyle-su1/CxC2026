from typing import Dict, Any
from app.agent.state import AgentState

from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
import json

def node_response_formulation(state: AgentState) -> Dict[str, Any]:
    """
    Node 5: Response Formulation (The "Speaker")
    """
    print("--- 5. Executing Response Node (The Speaker) ---")
    
    analysis = state.get('analysis_object', {})
    
    # Initialize Speaker Agent
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_REASONING, google_api_key=settings.GOOGLE_API_KEY)
    
    prompt = f"""
    You are a friendly, helpful shopping assistant. 
    Translate this technical analysis into a final recommendation JSON for the frontend.
    
    Analysis Data:
    {json.dumps(analysis, indent=2)}
    
    Create a "friendly_summary" that sounds human and helpful, referencing specific pros/cons.
    
    Return JSON:
    {{
        "outcome": "highly_recommended" or "consider_alternatives",
        "identified_product": "Name",
        "summary": "Friendly text...",
        "price_analysis": {{ ...From analysis... }},
        "community_sentiment": {{ ...From analysis... }},
        "alternatives": [ ...From analysis... ]
    }}
    """
    
    try:
        response = llm.invoke(prompt)
        content = response.content.replace('```json', '').replace('```', '').strip()
        final_payload = json.loads(content)
    except Exception as e:
        print(f"Response Error: {e}")
        final_payload = {
            "error": "Failed to generate response",
            "details": str(e)
        }
    
    return {"final_recommendation": final_payload}
