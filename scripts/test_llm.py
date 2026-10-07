import requests
import time
import json
import sys
from pathlib import Path

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from parseanything import parse
from parseanything.config import Options

def main():
    print("Testing local Ollama LLM integration...")
    opts = Options()
    
    # 1. Parse document locally to get the JSON payload
    print("Parsing sample_test.pdf...")
    doc = parse("sample_test.pdf", options=opts)
    doc_dict = doc.model_dump()
    
    # 2. Test /next-questions
    print("\n--- Testing /next-questions ---")
    try:
        res = requests.post("http://127.0.0.1:8000/next-questions", json=doc_dict)
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(res.json(), indent=2)}")
        
        questions = res.json().get("questions", [])
        if not questions:
            print("WARNING: No questions generated.")
            return
            
        first_q = questions[0]
    except Exception as e:
        print(f"Failed to fetch next questions: {e}")
        return
        
    # 3. Test /answer with the first question
    print(f"\n--- Testing /answer for question: '{first_q}' ---")
    try:
        payload = {
            "doc": doc_dict,
            "question": first_q
        }
        res = requests.post("http://127.0.0.1:8000/answer", json=payload)
        print(f"Status: {res.status_code}")
        print(f"Response: {json.dumps(res.json(), indent=2)}")
    except Exception as e:
        print(f"Failed to fetch answer: {e}")

if __name__ == "__main__":
    main()
