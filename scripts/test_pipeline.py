import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.manager_agent import run_pipeline

if __name__ == "__main__":
    brief = run_pipeline(scenario_id="demo_incident_01")
    print(f"\nCompleted incident: {brief.incident_id}")
    print(f"Overall confidence: {brief.overall_confidence}")
