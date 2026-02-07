from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI(title="Shopping Suggester API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.db.session import engine
from app.db.base import Base
from app.api.api import api_router

# Import the agent graph
# Assuming it's in app.agent.graph, created in a previous step or needing creation
try:
    from app.agent.graph import agent_app
except ImportError:
    # If graph.py doesn't exist yet, we can mock it or just pass for now
    # But user error log suggests they expect it to work
    print("Warning: Could not import agent_app from app.agent.graph")
    agent_app = None

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

class AnalyzeRequest(BaseModel):
    image: str # Base64 string
    user_preferences: Dict[str, Any]

@app.post("/analyze")
async def analyze_image(request: AnalyzeRequest):
    """
    Analyzes an uploaded image using the LangGraph agent.
    """
    if not agent_app:
        return {"error": "Agent not initialized"}

    initial_state = {
        "image_data": request.image,
        "user_preferences": request.user_preferences,
        "search_results": [],
        "reviews": [],
        "parsed_item": None,
        "verification_result": None,
        "final_recommendation": None,
        "reviews_summary": None
    }
    
    result = agent_app.invoke(initial_state)
    
    return result
