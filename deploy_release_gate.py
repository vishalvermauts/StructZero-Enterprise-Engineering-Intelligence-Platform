import subprocess
import sys
import os

def run_command(command, description):
    print(f"\n{'='*50}")
    print(f"Executing: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*50}\n")
    
    # Run the process and stream output to stdout
    process = subprocess.Popen(
        command,
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True,
        shell=True if os.name == 'nt' and command[0].startswith('snow') else False
    )
    process.wait()
    
    if process.returncode != 0:
        print(f"\n[FAILED] {description}")
        print(f"Aborting deployment pipeline due to error in {command[0]}.")
        sys.exit(process.returncode)
    else:
        print(f"\n[SUCCESS] {description}")

def main():
    print("Starting StructZero Release Gate Pipeline...")
    
    # Python executable from virtual env
    if os.name == 'nt':
        python_exe = os.path.join(".venv", "Scripts", "python.exe")
    else:
        python_exe = os.path.join(".venv", "bin", "python")
        
    if not os.path.exists(python_exe):
        # Fallback to current executable if virtual env structure isn't exactly as expected
        python_exe = sys.executable

    # Step 1: Run Pytest
    run_command([python_exe, "-m", "pytest", "tests/"], "Release Gate: Unit & Smoke Tests")
    
    # Step 2: Setup Snowflake CLI credentials
    run_command([python_exe, "setup_snow_cli.py"], "Configuration: Sync Snowflake Credentials")
    
    # Step 3: Deploy to Snowflake
    # Using shell=True for windows to find 'snow.cmd' in PATH if needed, 
    # but providing it directly works better usually. Let's just call 'snow'.
    snow_cmd = "snow"
    run_command([snow_cmd, "streamlit", "deploy", "--replace"], "Deployment: Push to Snowflake")
    
    print("\nPipeline completed successfully! Application is live.")

if __name__ == "__main__":
    main()
