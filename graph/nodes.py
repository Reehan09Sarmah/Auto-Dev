from sympy import content
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import AgentState
from tools.executor import execute_code_tests

load_dotenv()


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.3
)

# llm often generates python code in format ```python <code> ``` -> so we remove python and tick marks and keep the code
def convtorawdata(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:-1]
        text = "\n".join(lines)
    
    return text.strip()


def coder_node(state: AgentState) -> dict:
    print(f"CODER AGENT RUNNING --- Attempt: {state["retry_count"] + 1} ---")

    error_context = ""
    if state["error"]: # this is for retry
        error_context = f"\nYour previous code FAILED. Fix the code based on the ERROR:\n{state["error"]}\n. Preserve original task requirements"

    system_msg = (
        "You are an Expert Python Developer. "
        "Write clean, corect and executable python code. "
        "Follow the user's task and requirements exactly. "
        "Return only RAW Python code. "
        "No markdown fences. Strictly No Explanation. "
    )

    human_msg = f"Task:\n{state["task"]}\n{error_context}"
    

    messages = [
        SystemMessage(content=system_msg),
        HumanMessage(content=human_msg)
    ]

    response = llm.invoke(messages)
    code = convtorawdata(response)
    print(f"Generated {len(code.splitlines())} lines of code")

    return {"code" : code, "status": "running"}


    def tester_node(state: AgentState) -> dict:
        print(f"--- TESTER AGENT RUNNING ---")


        system_msg = (
            "You are an Expert Python Test Engineer. "
            "Write clean, corect pytest tests for the given python code. "
            "Import functions and classes from 'solution.py'. "
            "Cover normal cases, edge cases, and important failure cases. "
            "Return ONLY raw pytest code. "
            "No markdown fences. Strictly No explanations."
        )

        human_msg = f"Write pytest test for: \n{state['code']}"
        

        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=human_msg)
        ]

        response = llm.invoke(messages)
        tests = convtorawdata(response)
        print(f"Generated {len(tests.splitlines())} lines of tests")

        return {"tests" : tests}

