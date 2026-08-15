from typing import TypedDict

class AgentState(TypedDict):
    task: str
    code: str
    tests: str
    test_results: str
    error: str
    retry_count: int
    status: str