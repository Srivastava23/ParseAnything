import subprocess
import time
import requests
import json

# Start server
print("Starting server...")
proc = subprocess.Popen(["venv/bin/python", "parseanything/cli/main.py", "serve", "--port", "8001"])

# Wait for it to boot up
time.sleep(3)

try:
    print("Sending document to /parse...")
    with open("sample_test.pdf", "rb") as f:
        resp = requests.post("http://127.0.0.1:8001/parse", files={"file": f})
        
    print(f"Status Code: {resp.status_code}")
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    job_id = data.get("job_id")
    if job_id:
        print(f"\nPolling job {job_id}...")
        for _ in range(5):
            time.sleep(1)
            poll = requests.get(f"http://127.0.0.1:8001/jobs/{job_id}")
            poll_data = poll.json()
            print(f"Job Status: {poll_data['status']} - Progress: {poll_data['progress']}%")
            if poll_data['status'] == 'completed':
                print(f"Job completed successfully. Document has {poll_data['result']['stats']['pages']} pages.")
                break
except Exception as e:
    print(f"Error: {e}")
finally:
    # Kill the server
    proc.terminate()
    proc.wait()
    print("Server stopped.")
