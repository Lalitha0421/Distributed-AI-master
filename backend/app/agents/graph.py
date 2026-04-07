from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from app.agents.agent_state import AgentState
from app.agents.planner_agent import planner_agent
from app.agents.retriever_agent import retriever_agent
from app.agents.generator_agent import generator_agent
from app.agents.grader_agent import grader_agent

def create_knowledge_graph():
    """
    Constructs the LangGraph StateGraph for multi-agent knowledge retrieval.
    
    Flow: START -> Planner -> Retriever -> Generator -> Grader -> END
    """
    # ── Initialize the graph with our shared state ──────────────────────────
    builder = StateGraph(AgentState)
    
    # ── Add the agent nodes ───────────────────────────────────────────────
    builder.add_node("planner", planner_agent)
    builder.add_node("retriever", retriever_agent)
    builder.add_node("generator", generator_agent)
    builder.add_node("grader", grader_agent)
    
    # ── Define the edges (The Flow) ────────────────────────────────────────
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "retriever")
    builder.add_edge("retriever", "generator")
    builder.add_edge("generator", "grader")
    
    # ── Self-Correction Loop (Conditional Edge) ───────────────────────────
    def route_after_grader(state: AgentState) -> str:
        """Determines if the graph should loop back or finish."""
        if state.get("should_retry", False):
            return "retriever"
        return END

    builder.add_conditional_edges(
        "grader",
        route_after_grader,
        {
            "retriever": "retriever",
            END: END
        }
    )
    
    # ── Compile the graph into a runnable instance ──────────────────────────
    return builder.compile()

# Singleton instance
knowledge_graph = create_knowledge_graph()
