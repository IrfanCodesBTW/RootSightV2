from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.agents.manager_agent import run_pipeline

app = FastAPI(title="RootSight Backend")

@app.get("/api/incident/{scenario_id}")
def get_incident(scenario_id: str):
    """
    Run the incident analysis pipeline and return the brief.
    This will execute the agents sequentially.
    """
    try:
        # Run pipeline
        brief = run_pipeline(scenario_id=scenario_id)
        return brief.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# (Removed UI routes)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
