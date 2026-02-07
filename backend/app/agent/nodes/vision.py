from typing import Dict, Any
from app.agent.state import AgentState

def node_user_intent_vision(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: User Intent & Vision (The "Eye")
    
    Responsibilities:
    1. Identify primary item in screenshot using vision models.
    2. Extract relevant text (OCR) for context (price, store name).
    3. Return structured product query.
    
    Input: state['image_base64'], state['user_query']
    Output: state update with 'product_query'
    """
    print("--- 1. Executing Vision Node (The Eye) ---")
    
    # In a real implementation:
    # 1. client = google.cloud.vision.ImageAnnotatorClient()
    # 2. response = client.label_detection(image=state['image_base64'])
    # 3. response_text = client.text_detection(image=state['image_base64'])
    # 4. Use LLM to consolidate labels/text into a single product_query object.
    
    # Placeholder logic for "Sony WH-1000XM5" scenario
    # We pretend the vision model correctly identified the headphones.
    
    mock_product_identified = {
        "product_name": "Sony WH-1000XM5 Noise Canceling Headphones",
        "bounding_box": [100, 200, 500, 600],
        "context": "Amazon listing showing price $348",
        "ambiguity_resolved": True 
    }
    
    return {"product_query": mock_product_identified}
