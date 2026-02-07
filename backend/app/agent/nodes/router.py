from typing import Dict, Any
from app.agent.state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import logging

logger = logging.getLogger(__name__)

async def node_router(state: AgentState) -> Dict[str, Any]:
    """
    Classifies the user's intent to route to the appropriate node.
    
    Routes:
    - vision_search: New image → Node 1 (Vision)
    - chat: General conversation → End (respond only)
    - re_search: Visual/attribute prefs (color, style) → Node 2 (Market Scout)
    - re_analysis: Budget/price prefs (cheaper, $X) → Node 4 (Analysis)
    """
    logger.info("ROUTER: Determining intent...")
    
    user_query = state.get("user_query", "")
    image_base64 = state.get("image_base64")
    chat_history = state.get("chat_history", [])
    
    # 1. New Visual Search (Image + No History/First Message)
    if image_base64 and (not chat_history or len(chat_history) == 0):
        logger.info("ROUTER: New image detected -> vision_search")
        return {"router_decision": "vision_search"}

    # 2. Use LLM to classify intent for text/follow-ups
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    system_prompt = """You are the Router for a Shopping Assistant. Classify the user's latest message into ONE category:

    1. 'vision_search': User uploaded an image or wants to analyze a NEW product.
    2. 'chat': General conversation, questions about the current product, or small talk (e.g., "Hello", "Thanks", "Tell me more").
    3. 're_search': User wants DIFFERENT products based on visual preferences OR has a STRICT BUDGET. Examples:
       - "I don't like red" (color preference)
       - "Show me blue ones" 
       - "I prefer Nike brand"
       - "Something more modern looking"
       - "I only have $120" (STRICT budget - may need new products)
       - "My budget is $50" (STRICT budget)
    4. 're_analysis': User wants to RE-SCORE existing products based on GENERAL price preference (no specific dollar amount). Examples:
       - "Find cheaper ones"
       - "Show me the most affordable option"
       - "Price is important to me"
       - "My budget is tight" (vague, not specific)
    
    IMPORTANT: 
    - If user mentions COLOR, STYLE, BRAND, or LOOK -> 're_search'
    - If user specifies a SPECIFIC DOLLAR AMOUNT ($50, $120, etc.) -> 're_search' (may need new products)
    - If user says CHEAPER, AFFORDABLE, BUDGET-FRIENDLY (no specific amount) -> 're_analysis' (re-rank existing)
    
    Output ONLY the category name (one word).
    """
    
    human_prompt = f"""
    User Message: {user_query}
    Has Image: {bool(image_base64)}
    Chat History Length: {len(chat_history)}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        decision = await chain.ainvoke({})
        decision = decision.strip().lower()
        
        # Fallback for safety
        valid_decisions = ["vision_search", "chat", "re_search", "re_analysis"]
        if decision not in valid_decisions:
            logger.warning(f"ROUTER: Invalid decision '{decision}', defaulting to 'chat'")
            decision = "chat"
            
        logger.info(f"ROUTER: Decision -> {decision}")
        return {"router_decision": decision}
        
    except Exception as e:
        logger.error(f"ROUTER: Error in classification: {e}")
        return {"router_decision": "chat"} # Default fallback
