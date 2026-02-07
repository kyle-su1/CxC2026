from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import (
    node_user_intent_vision,
    node_discovery_runner,
    node_market_scout,
    node_skeptic_critique, 
    node_analysis_synthesis,
    node_response_formulation
)

# 1. Define the Graph
workflow = StateGraph(AgentState)

# 2. Add Nodes
# Each node function receives the current state and returns an update.
workflow.add_node("vision_node", node_user_intent_vision)
workflow.add_node("research_node", node_discovery_runner)
workflow.add_node("market_scout_node", node_market_scout)
workflow.add_node("skeptic_node", node_skeptic_critique)
workflow.add_node("analysis_node", node_analysis_synthesis)
workflow.add_node("response_node", node_response_formulation)

# 3. Define Edges (The Flow)
# Start -> Vision
workflow.set_entry_point("vision_node")

# Vision -> Research (Parallel Path 1)
workflow.add_edge("vision_node", "research_node")

# Vision -> Market Scout (Parallel Path 2)
workflow.add_edge("vision_node", "market_scout_node")

# Research -> Skeptic
workflow.add_edge("research_node", "skeptic_node")

# Market Scout -> Skeptic
workflow.add_edge("market_scout_node", "skeptic_node")

# Skeptic -> Analysis
workflow.add_edge("skeptic_node", "analysis_node")

# Analysis -> Response
workflow.add_edge("analysis_node", "response_node")

# Response -> End
workflow.add_edge("response_node", END)

# 4. Compile the Graph
agent_app = workflow.compile()
