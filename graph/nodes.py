import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import AgentState
from tools.executor import execute_code_tests
from tools.scanner import scan_code

load_dotenv()


MODELS = ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]

def call_llm(messages):
    for model_name in MODELS:
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=os.getenv("GEMINI_API_KEY"),
                temperature=0.3
            )
            response = llm.invoke(messages)
            print(f"  (Used model: {model_name})")
            return response
        except Exception as e:
            print(f"  Model {model_name} failed, trying next...")
            continue
    raise Exception("All models failed!")


# llm often generates python code in format ```python <code> ``` -> so we remove python and tick marks and keep the code
def convtorawdata(text: str) -> str:

     # Handle new Gemini models that return a list instead of string
    if isinstance(text, list):
        text = "\n".join(
            block["text"] for block in text if isinstance(block, dict) and "text" in block
        )
        
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:-1]
        text = "\n".join(lines)
    
    return text.strip()



# Coder
def coder_node(state: AgentState) -> dict:
    print(f"CODER AGENT RUNNING --- Attempt: {state['retry_count'] + 1} ---")

    error_context = ""
    if state['error']: # this is for retry
        error_context = f"\nYour previous code FAILED. Fix the code based on the ERROR:\n{state["error"]}\n. Preserve original task requirements"

    system_msg = (
        "You are an Expert Python Developer. "
        "Write clean, corect and executable python code. "
        "Follow the user's task and requirements exactly. "
        "Return only RAW Python code. "
        "No markdown fences. Strictly No Explanation. "
    )

    human_msg = f"Task:\n{state['task']}\n{error_context}"
    

    messages = [
        SystemMessage(content=system_msg),
        HumanMessage(content=human_msg)
    ]

    response = call_llm(messages)
    code = convtorawdata(response.content)
    print(f"Generated {len(code.splitlines())} lines of code")

    return {"code" : code, "status": "running"}



# Tester
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

    response = call_llm(messages)
    tests = convtorawdata(response.content)
    print(f"Generated {len(tests.splitlines())} lines of tests")

    return {"tests" : tests}



# Scanner Node
def scanner_node(state:AgentState) -> dict:
    print("--- Scanner Node Running ---")

    result = scan_code(state['code'])

    if result["safe"]:
        print("Code passed security scan. Sending it to execute")
        return {"status": "running"}
    else:
        issues_list = "\n".join(result['issues'])
        print(f"  SECURITY ISSUES FOUND:\n {issues_list}")
        error_msg = (
            f"SECURITY VIOLATION - Your code contains dangerous patterns:\n"
            f"{issues_list}\n\n"
            f"Rewrite the code to accomplish the task WITHOUT using these dangerous functions."
        )
        return {"error": error_msg, "status": "security_fail"}




# Executor
def executor_node(state: AgentState) -> dict:

    result = execute_code_tests(state['code'], state['tests'])
    print(result['output'])

    if result['passed']:
        print("ALL TEST PASSED")
        return {
            "test_results": result['output'],
            "error": "",
            "status": "pass"
        }
    else:
        new_count = state['retry_count'] + 1
        print(f"Test FAILED. Retry {new_count}/3")

        if new_count >= 3:
            print("Max retries reached! Human Intervention Necessary!")
            return {
                "test_results": result['output'],
                "error": result['output'],
                "retry_count": new_count,
                "status": "escalate",
            }

        return {
            "test_results": result['output'],
            "error": result['output'],
            "retry_count": new_count,
            "status": "fail"
        }
