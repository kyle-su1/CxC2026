from typing import Dict, Any
import os
import json
import base64
import google.generativeai as genai
from app.agent.state import AgentState

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

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
    log_file = "/app/debug_output.txt"
    
    def log_debug(message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{str(message)}\n")
        except Exception as e:
            print(f"Failed to write to log: {e}")

    log_debug("--- 1. Executing Vision Node (The Eye) ---")
    print("--- 1. Executing Vision Node (The Eye) ---")

    image_data = state.get("image_base64")
    user_query = state.get("user_query", "")
    
    log_debug(f"User Query: {user_query}")
    log_debug(f"Image Data Length: {len(image_data) if image_data else 0}")

    if not GOOGLE_API_KEY:
        log_debug("ERROR: GOOGLE_API_KEY not found.")
        print("ERROR: GOOGLE_API_KEY not found. Returning error.")
        return {"product_query": {"error": "Server configuration error: Vision model unavailable."}}

    if not image_data:
        log_debug("ERROR: No image data provided.")
        print("ERROR: No image data provided.")
        return {"product_query": {"error": "No image provided for analysis."}}

    try:
        # Clean base64 string if needed
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]

        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        log_debug("Image successfully decoded from base64.")
        
        # Prepare the model
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Construct prompt
        prompt = f"""
        Analyze this image and identify all distinct objects or products shown.
        For each object, provide its name and bounding box.
        Also extract any visible text that provides context like price, store name, or specifications.
        User's query/context: "{user_query}"

        Return ONLY a JSON object with this structure:
        {{
            "detected_objects": [
                {{
                    "name": "Name of object 1",
                    "bounding_box": [ymin, xmin, ymax, xmax], // Normalized 0-1000
                    "confidence": 0.95
                }},
                ...
            ],
            "product_name": "Name of the MAIN/PRIMARY product intent",
            "context": "Any text/price/store info visible",
            "ambiguity_resolved": true/false
        }}
        """

        # Generate content
        log_debug("Sending request to Gemini model...")
        response = model.generate_content([
            {'mime_type': 'image/jpeg', 'data': image_bytes},
            prompt
        ])
        try:
            # Clean up JSON markdown
            content = response.text.replace('```json', '').replace('```', '').strip()
            product_data = json.loads(content)
            
            log_debug(f"Gemini Response: {json.dumps(product_data, indent=2)}")
            
        except Exception as e:
            print(f"Vision Node Error (Gemini): {e}")
            log_debug(f"Vision Node Error (Gemini): {e}")
            product_data = {
                "product_name": "Unknown Item", 
                "bounding_box": [0,0,0,0],
                "detected_objects": []
            }


        # --- GOOGLE LENS INTEGRATION (DISABLED) ---
        # Public URL required for SerpAPI Lens. Using Gemini Bounding Box instead.
        lens_data = {}

        return {
            "product_query": {
                "canonical_name": product_data.get('product_name'),
                "context": product_data.get('context'),
                "detected_objects": product_data.get('detected_objects', []),
                # "lens_data": lens_data
            },
            "bounding_box": product_data.get('bounding_box') # Keep main box for compat
        }

    except Exception as e:
        log_debug(f"EXCEPTION in vision node: {str(e)}")
        print(f"Error in vision analysis: {e}")
        # Fallback to a generic error or empty result so the pipeline doesn't crash hard
        return {"product_query": {
            "product_name": "Unknown Item",
            "context": f"Error analyzing image: {str(e)}",
            "ambiguity_resolved": False
        }}
