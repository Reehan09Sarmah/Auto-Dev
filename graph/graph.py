from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes import coder_node, tester_node, executor_node, scanner_node

# router for the agentic loop based on conditions
def route_after_execution(state: AgentState) -> str:
    if state["status"] == "pass":
        return "pass"
    elif state["status"] == "escalate":
        return "escalate"
    else:
        return "retry"

def route_after_scan(state: AgentState) -> str:
    if state["status"] == "security_fail":
        return "security_fail"
    
    return "safe"


# the graph
def build_graph():
    flow = StateGraph(AgentState)

    # Register nodes
    flow.add_node("coder", coder_node)
    flow.add_node("tester", tester_node)
    flow.add_node("scanner", scanner_node)
    flow.add_node("executor", executor_node)

    flow.set_entry_point("coder") # the starting agent based on user prompt

    # edges between agentic functions - from A to go to B
    flow.add_edge("coder", "tester")
    flow.add_edge("tester", "scanner")


    # conditional movements
    flow.add_conditional_edges(
        "scanner",
        route_after_scan,
        {
            "safe": "executor",
            "security_fail": "coder"
        }
    )

    
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