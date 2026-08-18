import subprocess
import tempfile
import os
import sys

def execute_code_tests(code:str, tests:str) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = os.path.join(tmpdir, "solution.py")
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(code)

        # now the tests
        test_path = os.path.join(tmpdir, 'tests_sol.py')
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(tests)

        # run the tests on the solution using pytest | -v = verbose | --tb=short : short error tracebacks
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests_sol.py", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=50,
                cwd=tmpdir
            )

            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            
            return {
                "output": output,
                "passed": result.returncode == 0,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "output":"ERROR: Timeout Exceeded",
                "passed": False,
                "returncode": -1
            }


