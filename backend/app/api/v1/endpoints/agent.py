import os
import base64
import json
import io
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
from PIL import Image
from pillow_heif import register_heif_opener

# Enable HEIC support
register_heif_opener()

router = APIRouter()

# Lazy-loaded OpenAI client (via OpenRouter)
_openai_client = None

def get_openai_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENROUTER_OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENROUTER_OPENAI_API_KEY not found in environment")
        _openai_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "ShoppingSuggester",
            },
        )
    return _openai_client


class ImageAnalysisRequest(BaseModel):
    imageBase64: str


class DetectedObject(BaseModel):
    name: str
    score: float
    openAiLabel: Optional[str] = None
    boundingPoly: Optional[dict] = None


class ImageAnalysisResponse(BaseModel):
    objects: List[DetectedObject]
    labels: List[dict] = []


@router.post("/analyze-image")
async def analyze_image(request: ImageAnalysisRequest):
    """
    Trigger the Full Agent Workflow:
    1. Vision (Gemini 2.0 Flash)
    2. Research (Tavily)
    3. Market Scout
    4. Skeptic Analysis
    5. Final Response
    """
    print("\n--- Starting Full Agent Workflow ---")
    
    if not request.imageBase64:
        raise HTTPException(status_code=400, detail="No image data provided")

    # Clean base64 string
    base64_data = request.imageBase64
    if "base64," in base64_data:
        base64_data = base64_data.split("base64,")[1]

    # Initialize Agent State
    initial_state = {
        "user_query": "Identify this product and find the best price and alternatives.",
        "image_base64": base64_data,
        "user_preferences": {},  # Default preferences
        "product_query": {},
        "research_data": {},
        "market_scout_data": {},
        "risk_report": {},
        "analysis_object": {},
        "alternatives_analysis": [],
        "final_recommendation": {}
    }

    try:
        # Import the graph here to avoid circular dependencies at module level if any
        from app.agent.graph import agent_app
        
        # Invoke the graph
        # This runs all nodes: Vision -> Research/Scout -> Skeptic -> Analysis -> Response
        final_state = await agent_app.ainvoke(initial_state)
        
        result = final_state.get("final_recommendation", {})
        
        if not result:
            print("WARNING: Graph completed but returned empty final_recommendation.")
            # Fallback
            return {
                "outcome": "error",
                "summary": "The agent completed analysis but returned no data.",
                "active_product": {"name": "Unknown", "detected_objects": []}
            }
            
        return result

    except Exception as e:
        print(f"Error executing agent workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")


class RecommendationRequest(BaseModel):
    user_preferences: dict
    current_item_context: Optional[dict] = None


class RecommendationResponse(BaseModel):
    items: List[dict]


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_items(request: RecommendationRequest):
    # This endpoint can be used for follow-up refinements
    # For now, it's a placeholder or can reuse the graph with updated preferences
    return {
        "items": []
    }


class ChatAnalyzeRequest(BaseModel):
    """Request for chat-based targeted object analysis."""
    image_base64: str
    user_query: str
    chat_history: List[dict] = []


class ChatAnalyzeResponse(BaseModel):
    """Response with targeted object info and chat response."""
    chat_response: str
    targeted_object_name: Optional[str] = None
    targeted_bounding_box: Optional[List[float]] = None  # [ymin, xmin, ymax, xmax]
    confidence: Optional[float] = None
    analysis: Optional[dict] = None


@router.post("/chat-analyze", response_model=ChatAnalyzeResponse)
async def chat_analyze(request: ChatAnalyzeRequest):
    """
    Chat-based targeted object analysis.
    
    User asks about a specific item in the image (e.g., "what is this phone?").
    The LLM identifies the target object, returns its bounding box, 
    and provides a chat response.
    """
    import os
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    
    print(f"[ChatAnalyze] Query: {request.user_query}")
    
    if not request.image_base64:
        raise HTTPException(status_code=400, detail="No image data provided")
    
    # Clean base64 string
    base64_data = request.image_base64
    if "base64," in base64_data:
        base64_data = base64_data.split("base64,")[1]
    
    try:
        # Use Gemini Vision to analyze the query and find target object
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        # Prompt to extract object and find bounding box
        system_prompt = """You are a visual shopping assistant. The user has uploaded an image and is asking about a specific item.

Your task:
1. Understand what object the user is asking about from their query
2. Locate that SPECIFIC object in the image
3. Return the bounding box for ONLY that object

Return a JSON response with:
- "target_object": the name/description of the object the user is asking about
- "bounding_box": [y_min, x_min, y_max, x_max] as decimals 0.0-1.0 (normalized coordinates)
- "confidence": 0.0-1.0 confidence in finding this object  
- "chat_response": a brief, friendly response acknowledging you found the item

If you cannot identify the target object, set bounding_box to null and explain in chat_response.

Return ONLY valid JSON, no markdown."""

        human_prompt = f"""User Query: {request.user_query}

Look at the image and find the object the user is asking about. Return the bounding box for ONLY that specific item."""

        # Create multimodal message
        from langchain_core.messages import HumanMessage
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": system_prompt + "\n\n" + human_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}
                }
            ]
        )
        
        response = await llm.ainvoke([message])
        response_text = response.content.strip()
        
        # Clean markdown if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            if len(lines) >= 3:
                response_text = "\n".join(lines[1:-1])
        
        print(f"[ChatAnalyze] LLM Response: {response_text[:200]}...")
        
        # Parse JSON response
        result = json.loads(response_text)
        
        return ChatAnalyzeResponse(
            chat_response=result.get("chat_response", "I'm looking at your image..."),
            targeted_object_name=result.get("target_object"),
            targeted_bounding_box=result.get("bounding_box"),
            confidence=result.get("confidence", 0.8)
        )
        
    except json.JSONDecodeError as e:
        print(f"[ChatAnalyze] JSON parse error: {e}")
        return ChatAnalyzeResponse(
            chat_response="I had trouble analyzing the image. Could you try asking again?",
            targeted_object_name=None,
            targeted_bounding_box=None
        )
    except Exception as e:
        print(f"[ChatAnalyze] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat analysis failed: {str(e)}")
