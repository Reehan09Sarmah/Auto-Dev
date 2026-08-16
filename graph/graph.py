from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes import coder_node, tester_node, executor_node

# router for the agentic loop based on conditions
def route_after_execution(state: AgentState) -> str:
    if state["status"] == "pass":
        return "pass"
    elif state["status"] == "escalate":
        return "escalate"
    else:
        return "retry"


# the graph
def build_graph():
    flow = StateGraph(AgentState)

    # Register nodes
    flow.add_node("coder", coder_node)
    flow.add_node("tester", tester_node)
    flow.add_node("executor", executor_node)

    flow.set_entry_point("coder") # the starting agent based on user prompt

    # edges between agentic functions - from A to go to B
    flow.add_edge("coder", "tester")
    flow.add_edge("tester", "executor")

    # conditional movement
    flow.add_conditional_edges(
        "executor",
        route_after_execution,
        {
            "pass": END,
            "escalate": END,
            "retry": "coder"
        }
    )

    return flow.compile()