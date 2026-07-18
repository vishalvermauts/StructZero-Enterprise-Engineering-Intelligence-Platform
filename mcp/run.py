import subprocess
import sys
import os

def main():
    # Ensure we use the .venv python if available
    venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "python.exe"))
    
    server_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "server.py"))
    
    # If run.py is executed via the venv directly, sys.executable might already be correct.
    # But just to be safe, if we find .venv/Scripts/python.exe, use it.
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable
    
    # We must preserve stdin/stdout for MCP stdio protocol
    subprocess.run([python_exe, server_script])

if __name__ == "__main__":
    main()
