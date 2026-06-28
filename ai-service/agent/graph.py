"""
graph.py - LanGraph agent graph
Wires the three nodes together into a linear flow:
classify -> execute -> respond
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Any
from agent.nodes import classify_node, execute_node, respond_node

# state definition
# this is the data that flows between nodes
class AgentState(TypedDict):
    message: str
    tool: str
    params: dict
    reasoning: str
    tool_result: Any
    response: str

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify", classify_node)
    graph.add_node("execute", execute_node)
    graph.add_node("respond", respond_node)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "execute")
    graph.add_edge("execute", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


agent = build_graph()


def run_agent(message: str) -> dict: 
    """
    Run the agent with a user message.
    Returns the full state including response.

    Args: 
        message: User's question in plain English

    Returns:
        dict with response, tool, params, reasoning
    """

    initial_state = AgentState({
        "message": message,
        "tool": "",
        "params": {},
        "reasoning": "",
        "tool_result": None,
        "response": ""
    })

    result = agent.invoke(initial_state)

    return {
        "response": result["response"],
        "tool_used": result["tool"],
        "params": result["params"],
        "reasoning": result["reasoning"]
    }