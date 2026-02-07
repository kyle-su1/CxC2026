from typing import Dict, Any, List
from app.agent.state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.preference_service import get_user_explicit_preferences, merge_weights
# from app.db.session import SessionLocal # Avoid circular import if possible, use dependency injection pattern or import inside
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
import json
import os
import logging

logger = logging.getLogger(__name__)

async def node_chat(state: AgentState) -> Dict[str, Any]:
    """
    Node 6: Chat
    Handles general conversation and preference updates.
    """
    logger.info("--- Executing Chat Node ---")
    
    user_query = state.get("user_query")
    router_decision = state.get("router_decision")
    chat_history = state.get("chat_history", [])
    session_id = state.get("session_id")
    
    # 1. Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.7,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # 2. Handle Preference Updates
    if router_decision == "update_preferences":
        logger.info("CHAT: Updating preferences based on user input")
        
        # Extract preferences using LLM
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Preference Extractor. Analyze the user's message and extract preferences into a JSON object.
            
            Supported keys:
            - price_sensitivity (0.0 to 1.0, 1.0 = highly sensitive/wants cheap)
            - quality (0.0 to 1.0)
            - eco_friendly (0.0 to 1.0)
            - brand_reputation (0.0 to 1.0)
            
            Example: "I hate red, and I want something cheap."
            Output: {"price_sensitivity": 0.9} (Note: color prefs are handled elsewhere, here we focus on weights. If color is mentioned, ignore for now or add to metadata if supported.)
            
            Return ONLY the JSON.
            """),
            ("human", "{user_query}")
        ])
        
        chain = extraction_prompt | llm | StrOutputParser()
        try:
            result = await chain.ainvoke({"user_query": user_query})
            # Clean up potential markdown formatting
            cleaned_result = result.strip()
            if cleaned_result.startswith("```"):
                # Remove first line (```json or ```) and last line (```)
                lines = cleaned_result.split("\n")
                if len(lines) >= 3:
                    cleaned_result = "\n".join(lines[1:-1])
            
            new_prefs = json.loads(cleaned_result)
            
            # Update DB
            # We need user_id from somewhere. In a real app, it's in the session or context.
            # For now, we'll try to find a user_id from the session if we had it, or just Mock it/Log it.
            # Assuming we can get a DB session:
            with SessionLocal() as db:
                # Mock User ID 1 for MVP or try to get from state/session
                # In the `session` model, we have `user_id`.
                # We need to fetch the session object to get the user_id.
                from app.models.session import Session as SessionModel
                from app.models.user import User
                
                if session_id:
                    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
                    if session_obj and session_obj.user_id:
                        user = db.query(User).filter(User.id == session_obj.user_id).first()
                        if user:
                            current_prefs = user.preferences or {}
                            current_prefs.update(new_prefs)
                            user.preferences = current_prefs
                            db.commit()
                            logger.info(f"CHAT: Updated preferences for user {user.id}: {new_prefs}")
                            
                            # Merge into current state
                            state_prefs = state.get("user_preferences", {})
                            state_prefs.update(new_prefs)
                            state["user_preferences"] = state_prefs
            
        except Exception as e:
            logger.error(f"CHAT: Failed to update preferences: {e}")

    # 3. Generate Response
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

    # Context could come from analysis_object if available
    analysis = state.get("analysis_object")
    
    system_text = """You are a helpful Shopping Assistant. 
    You have access to the user's current analysis session.
    
    If the user just updated their preferences, confirm it.
    If the user is asking a question about the product, answer it based on the analysis.
    If the user is just chatting, be friendly.
    
    Keep responses concise and helpful.
    """
    
    if analysis:
        # We append this directly. Even if it has {}, it won't be templated if we use SystemMessage directly.
        system_text += f"\n\nCurrent Analysis Context: {str(analysis)}"
    
    # helper to map role to message class
    def map_message(role, content):
        if role == "user":
            return HumanMessage(content=content)
        elif role == "assistant":
            return AIMessage(content=content)
        elif role == "system":
            return SystemMessage(content=content)
        return HumanMessage(content=content)

    # Build messages list
    messages = [SystemMessage(content=system_text)]
    
    # Add recent history (last 5 messages)
    for msg in chat_history[-5:]:
        messages.append(map_message(msg.get("role"), msg.get("content")))
    
    messages.append(HumanMessage(content=user_query))
    
    # Invoke LLM directly with messages
    # We use StrOutputParser to get string response
    chain = llm | StrOutputParser()
    response = await chain.ainvoke(messages)
    
    return {
        "chat_history": chat_history + [{"role": "user", "content": user_query}, {"role": "assistant", "content": response}],
        "final_recommendation": {"chat_response": response},
        # Determine loop step
        "loop_step": "analysis_node" if router_decision == "update_preferences" else "end"
    }
