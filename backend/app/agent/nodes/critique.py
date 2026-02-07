from typing import Dict, Any
from app.agent.state import AgentState

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.core.config import settings
import json

def node_skeptic_critique(state: AgentState) -> Dict[str, Any]:
    """
    Node 3: The Skeptic (Critique & Verification)
    """
    print("--- 3. Executing Critique Node (The Skeptic) ---")
    
    research_results = state.get('research_data', {})
    
    # Initialize Skeptic Agent
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_REASONING, google_api_key=settings.GOOGLE_API_KEY)
    
    prompt = f"""
    You are a cynical, skeptical shopping assistant. Your job is to find flaws, fake reviews, and pricing tricks.
    
    Analyze this research data:
    {json.dumps(research_results, indent=2)}
    
    Return a JSON object:
    {{
        "fake_review_likelihood": "High/Medium/Low + explanation",
        "price_integrity": "Is it a real deal or markup?",
        "hidden_flaws": ["List of specific complaints found"]
    }}
    """
    
    try:
        response = llm.invoke(prompt)
        content = response.content.replace('```json', '').replace('```', '').strip()
        risk_report = json.loads(content)
    except Exception as e:
        print(f"Skeptic Error: {e}")
        risk_report = {
            "fake_review_likelihood": "Unknown",
            "hidden_flaws": ["Could not analyze risks due to error"]
        }
    
    return {"risk_report": risk_report}
