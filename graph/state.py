from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    task: str
    code: str
    tests: str
    test_results: str
    error: str
    retry_count: int
    status: str
    observe: Annotated[dict, operator.ior]
    subtasks: list[str]
    current_subtask_index: int
    completed_code: str



