import subprocess
import json
import sys
import time

def main():
    print("Starting MCP Server...")
    # Start the MCP server process
    process = subprocess.Popen(
        [sys.executable, "mcp/run.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    def send_request(req):
        print(f"Sending: {json.dumps(req)}")
        process.stdin.write(json.dumps(req) + "\n")
        process.stdin.flush()
        
    def read_response():
        line = process.stdout.readline()
        if line:
            print(f"Received: {line.strip()}")
            return json.loads(line)
        return None

    try:
        # 1. Initialize
        send_request({
            "jsonrpc": "2.0", 
            "id": 1, 
            "method": "initialize", 
            "params": {
                "protocolVersion": "2024-11-05", 
                "capabilities": {}, 
                "clientInfo": {"name": "test-client", "version": "1.0"}
            }
        })
        
        res = read_response()
        
        # 2. Initialized Notification
        send_request({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        })
        
        # 3. List Tools
        send_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        })
        
        res = read_response()
        
        # 4. Call list_projects tool
        send_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "list_projects",
                "arguments": {}
            }
        })
        
        # Wait a moment for snowflake to return
        time.sleep(2)
        res = read_response()
        
    finally:
        process.terminate()
        print("MCP Server terminated.")

if __name__ == "__main__":
    main()
