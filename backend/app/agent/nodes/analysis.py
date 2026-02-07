from typing import Dict, Any, Optional
from app.agent.state import AgentState

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.core.config import settings
import json

def node_analysis_synthesis(state: AgentState) -> Dict[str, Any]:
    """
    Node 4: Analysis & Synthesis (The "Brain")
    """
    print("--- 4. Executing Analysis Node (The Brain) ---")
    
    research = state.get('research_data', {})
    risk = state.get('risk_report', {})
    prefs = state.get('user_preferences', {})
    product_query = state.get('product_query', {})
    
    # Initialize Analyst Agent
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_REASONING, google_api_key=settings.GOOGLE_API_KEY)
    
    prompt = f"""
    You are an expert product analyst. Synthesize the following data to provide a recommendation.
    
    Product Identified: {product_query.get('product_name')}
    User Preferences: {prefs}
    Research Data: {json.dumps(research, indent=2)}
    Risk Report: {json.dumps(risk, indent=2)}
    
    Calculate a match score (0.0 to 1.0) based on how well the product fits the user preferences.
    Identify any alternatives if mentioned in research.
    
    Return JSON:
    {{
        "match_score": 0.85, 
        "product_identified": "Name",
        "price_analysis": {{ "current": Price, "verdict": "Good/Bad" }},
        "community_sentiment": {{ "summary": "...", "warnings": [...] }},
        "alternatives": [ {{ "name": "...", "match_score": 0.0, "reason": "..." }} ]
    }}
    """
    
    try:
        response = llm.invoke(prompt)
        content = response.content.replace('```json', '').replace('```', '').strip()
        analysis_object = json.loads(content)
    except Exception as e:
        print(f"Analysis Error: {e}")
        analysis_object = {
            "match_score": 0.0,
            "product_identified": "Error",
            "community_sentiment": {"summary": "Analysis failed", "warnings": []}
        }
    
    return {"analysis_object": analysis_object}
