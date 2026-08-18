import re

DANGEROUS_PATTERNS = [
    (r'\bos\.system\s*\(',      'os.system() -- direct shell command execution'),
    (r'\bsubprocess\.call\s*\(','subprocess.call() -- shell command execution'),
    (r'\bsubprocess\.Popen\s*\(','subprocess.Popen() -- shell process spawning'),
    (r'\beval\s*\(',            'eval() -- executes arbitrary strings as code'),
    (r'\bexec\s*\(',            'exec() -- executes arbitrary strings as code'),
    (r'\b__import__\s*\(',      '__import__() -- dynamic import, possible injection'),
    (r'\bshutil\.rmtree\s*\(',  'shutil.rmtree() -- recursive directory deletion'),
    (r'rm\s+-rf',               'rm -rf -- destructive shell command in string'),
]

# scan code for dangerous code
def scan_code(code:str) -> dict:
    issues = []
    lines = code.split('\n')

    for idx, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line.startswith("#"): continue # it's a comment and it won't do any harm

        for pattern, desc in DANGEROUS_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(f"Line {idx}: {desc}")
                
        
    if issues:
        return {"safe": False, "issues": issues}
    
    return {"safe": True, "issues": []}