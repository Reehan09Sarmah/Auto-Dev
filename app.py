"""
AutoDev Flask App - Terminal UI with SSE Streaming
Only sends structured phase events to the browser, not raw print output.
"""
import sys
import io
import threading
import queue
import json
import re
from flask import Flask, render_template, request, Response
from dotenv import load_dotenv
from graph.graph import build_graph

load_dotenv()

app = Flask(__name__)
graph = build_graph()


class FilteredWriter(io.TextIOBase):
    """
    Captures print() output and converts it into structured phase events.
    Raw log noise is filtered out; only meaningful status changes are sent.
    """
    def __init__(self, q, original_stdout):
        self.q = q
        self.original = original_stdout
        self.buffer = ""

    def write(self, text):
        if not text:
            return 0
        # Also write to real stdout for server-side debugging
        self.original.write(text)
        self.buffer += text
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            self._classify(line.strip())
        return len(text)

    def flush(self):
        self.original.flush()
        if self.buffer.strip():
            self._classify(self.buffer.strip())
            self.buffer = ""

    def _classify(self, line):
        if not line:
            return
        # Coder starting
        if line.startswith("CODER AGENT RUNNING"):
            attempt = "1"
            m = re.search(r"Attempt:\s*(\d+)", line)
            if m:
                attempt = m.group(1)
            self.q.put(json.dumps({"type": "phase", "phase": "coder", "status": "running", "detail": f"Attempt {attempt}"}))

        # RAG retrieval
        elif line.startswith("[RAG] Retrieved"):
            chunks = re.search(r"(\d+)", line)
            n = chunks.group(1) if chunks else "?"
            self.q.put(json.dumps({"type": "phase", "phase": "rag", "status": "done", "detail": f"{n} doc chunks retrieved"}))

        elif line.startswith("[RAG] No relevant"):
            self.q.put(json.dumps({"type": "phase", "phase": "rag", "status": "done", "detail": "No docs matched"}))

        # Coder finished generating
        elif line.startswith("Generated") and "lines of code" in line:
            self.q.put(json.dumps({"type": "phase", "phase": "coder", "status": "done", "detail": line}))

        # Tester starting
        elif "TESTER AGENT RUNNING" in line:
            self.q.put(json.dumps({"type": "phase", "phase": "tester", "status": "running", "detail": "Writing tests..."}))

        # Tester finished generating
        elif line.startswith("Generated") and "lines of tests" in line:
            self.q.put(json.dumps({"type": "phase", "phase": "tester", "status": "done", "detail": line}))

        # Scanner
        elif "Scanner Node Running" in line:
            self.q.put(json.dumps({"type": "phase", "phase": "scanner", "status": "running", "detail": "Scanning for vulnerabilities..."}))

        elif "Code passed security scan" in line:
            self.q.put(json.dumps({"type": "phase", "phase": "scanner", "status": "done", "detail": "Passed security scan"}))

        elif "SECURITY ISSUES FOUND" in line:
            self.q.put(json.dumps({"type": "phase", "phase": "scanner", "status": "fail", "detail": "Security issues detected"}))

        # Executor results
        elif "ALL TEST PASSED" in line:
            self.q.put(json.dumps({"type": "phase", "phase": "executor", "status": "done", "detail": "All tests passed"}))

        elif line.startswith("Test FAILED"):
            self.q.put(json.dumps({"type": "phase", "phase": "executor", "status": "fail", "detail": line}))

        # Individual test progress (e.g. "test_sum PASSED  [ 33%]")
        elif "PASSED" in line or "FAILED" in line:
            pct = re.search(r"\[\s*(\d+)%\]", line)
            tname = re.search(r"::(\w+)", line)
            if pct:
                name = tname.group(1) if tname else "test"
                status = "done" if "PASSED" in line else "fail"
                self.q.put(json.dumps({"type": "test", "name": name, "passed": "PASSED" in line, "pct": int(pct.group(1))}))

        # Test count line from pytest
        elif "passed" in line and ("failed" in line or "error" in line or line.strip().startswith("=")):
            m = re.search(r"(\d+)\s+passed", line)
            f = re.search(r"(\d+)\s+failed", line)
            if m:
                detail = f"{m.group(1)} passed"
                if f:
                    detail += f", {f.group(1)} failed"
                self.q.put(json.dumps({"type": "phase", "phase": "executor", "status": "running", "detail": detail}))

        elif line.strip().startswith("=") and "passed" in line:
            m = re.search(r"(\d+)\s+passed", line)
            if m:
                self.q.put(json.dumps({"type": "phase", "phase": "executor", "status": "running", "detail": f"{m.group(1)} tests passed"}))


@app.route("/")
def index():
    return render_template("index.html")


def run_agent(task, q):
    """Run the LangGraph agent in a background thread."""
    original_stdout = sys.stdout
    sys.stdout = FilteredWriter(q, original_stdout)

    try:
        start_state = {
            "task": task,
            "code": "",
            "tests": "",
            "test_results": "",
            "error": "",
            "retry_count": 0,
            "status": "running",
            "observe": {}
        }

        # Signal that execution has started
        q.put(json.dumps({"type": "phase", "phase": "executor", "status": "running", "detail": "Running tests..."}))

        end_state = graph.invoke(start_state)

        # Send final status
        if end_state["status"] == "pass":
            q.put(json.dumps({"type": "result", "status": "pass", "code": end_state["code"]}))
        elif end_state["status"] == "escalate":
            q.put(json.dumps({"type": "result", "status": "escalate", "code": end_state.get("code", ""), "error": end_state.get("error", "")}))
        elif end_state["status"] == "security_fail":
            q.put(json.dumps({"type": "result", "status": "security_fail", "error": end_state.get("error", "")}))

        # Send observability data
        obs = end_state.get("observe", {})
        q.put(json.dumps({
            "type": "obs",
            "coder_time": obs.get("coder_time", 0),
            "coder_tokens": obs.get("coder_tokens", 0),
            "tester_time": obs.get("tester_time", 0),
            "tester_tokens": obs.get("tester_tokens", 0),
            "retries": end_state.get("retry_count", 0)
        }))

    except Exception as e:
        q.put(json.dumps({"type": "error", "message": str(e)}))
    finally:
        sys.stdout = original_stdout
        q.put("[DONE]")


@app.route("/run")
def run():
    task = request.args.get("task", "").strip()
    if not task:
        return Response("data: [DONE]\n\n", content_type="text/event-stream")

    q = queue.Queue()
    thread = threading.Thread(target=run_agent, args=(task, q), daemon=True)
    thread.start()

    def generate():
        while True:
            try:
                line = q.get(timeout=180)
                yield f"data: {line}\n\n"
                if line == "[DONE]":
                    break
            except queue.Empty:
                yield 'data: {"type":"error","message":"Timed out"}\n\n'
                yield "data: [DONE]\n\n"
                break

    return Response(generate(), content_type="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)