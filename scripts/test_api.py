import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_pipeline():
    print("Triggering pipeline...")
    payload = {"bundle_file": "db_connection_pool.json"}
    resp = requests.post(f"{BASE_URL}/api/trigger", json=payload)
    if resp.status_code != 200:
        print(f"Trigger failed: {resp.status_code} - {resp.text}")
        return
    
    data = resp.json()
    incident_id = data["data"]["incident_id"]
    print(f"Incident ID: {incident_id}")
    
    # Poll for completion
    for _ in range(30):
        time.sleep(2)
        resp = requests.get(f"{BASE_URL}/api/incident/{incident_id}")
        if resp.status_code != 200:
            print(f"Poll failed: {resp.status_code}")
            break
        
        state = resp.json()["data"]
        print(f"Status: {state['status']}")
        if state["status"] in ["completed", "failed"]:
            print(json.dumps(state, indent=2))
            break
    else:
        print("Polling timed out.")

if __name__ == "__main__":
    test_pipeline()
