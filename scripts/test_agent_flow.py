import asyncio
import base64
from app.agent.graph import agent_app
from app.core.config import settings

# Sample base64 image (small 1x1 pixel) just to pass valid format if needed
# In reality, you'd load a real image
SAMPLE_IMAGE = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

async def test_agent():
    print("--- Starting Agent Flow Test ---")
    
    # ensure keys are present
    if "your_" in settings.GOOGLE_API_KEY:
        print("WARNING: API Keys not set in .env. Real calls will fail.")
    else:
        print("API Keys detected. Proceeding with real calls...")

    initial_state = {
        "user_query": "Is this a good deal for office work?",
        "image_base64": SAMPLE_IMAGE,
        "user_preferences": {
            "price_sensitivity": 0.5,
            "quality": 0.8,
            "brand_loyalty": 0.2
        }
    }

    try:
        # Using .invoke() for synchronous execution in this script, 
        # but inside async def we could use .ainvoke() if we were fully async
        result = await agent_app.ainvoke(initial_state)
        
        print("\n--- Final Recommendation ---")
        print(result.get("final_recommendation", "No result found"))
        
    except Exception as e:
        print(f"\nError running agent: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())
