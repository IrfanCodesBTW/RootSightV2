import asyncio
import os
import json
from rootsight.backend.pipeline_orchestrator import start_pipeline, get_pipeline_state

async def precompute():
    scenarios = [
        "cdn_502_incident.json",
        "payment_api_cpu.json",
        "db_connection_pool.json"
    ]
    
    print("Pre-computing demo scenarios...")
    
    for scenario in scenarios:
        print(f"\nStarting {scenario}...")
        try:
            incident_id = await start_pipeline({"bundle_file": scenario})
            
            # Poll until complete
            while True:
                state = get_pipeline_state(incident_id)
                if state and state["status"] in ["completed", "failed"]:
                    break
                await asyncio.sleep(2)
                
            print(f"Finished {scenario}. Final status: {state['status']}")
            
            # Cache the result to a file if needed for pure offline demo
            cache_dir = os.path.join(os.path.dirname(__file__), "data", "cached_runs")
            os.makedirs(cache_dir, exist_ok=True)
            
            with open(os.path.join(cache_dir, f"cached_{scenario}"), "w") as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            print(f"Error processing {scenario}: {e}")

if __name__ == "__main__":
    asyncio.run(precompute())
