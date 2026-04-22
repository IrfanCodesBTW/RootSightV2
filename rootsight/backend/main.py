import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import settings
from .pipeline_orchestrator import start_pipeline, get_pipeline_state, get_all_incidents
from .storage.database import create_db_and_tables
from .api_response import success_response, error_response

logger = logging.getLogger(__name__)
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

app = FastAPI(title="RootSight API", version="0.1.0")

@app.on_event("startup")
def on_startup():
    logger.info("startup.begin")
    create_db_and_tables()
    logger.info("startup.complete")


def _cors_origins() -> list[str]:
    origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
    return origins or ["http://localhost:3000"]


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("request_validation_failed path=%s errors=%s", request.url.path, exc.errors())
    return JSONResponse(status_code=422, content=error_response("Invalid request payload."))


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    message = str(exc.detail) if exc.detail else "Request failed."
    logger.error("http_exception path=%s status=%s detail=%s", request.url.path, exc.status_code, message)
    return JSONResponse(status_code=exc.status_code, content=error_response(message))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception path=%s", request.url.path)
    message = "Internal server error."
    if settings.API_ERROR_DETAIL_IN_RESPONSE:
        message = str(exc)
    return JSONResponse(status_code=500, content=error_response(message))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return success_response({"message": "RootSight API is operational", "version": "0.1.0"})

@app.get("/health")
async def health():
    return success_response({"status": "healthy"})

@app.post("/api/trigger")
async def trigger_pipeline(payload: dict[str, Any]):
    """
    Triggers the RootSight intelligence pipeline.
    Accepts PagerDuty/Datadog payloads, or a `bundle_file` for demo data.
    """
    if not isinstance(payload, dict) or not payload:
        raise HTTPException(status_code=422, detail="Payload must be a non-empty JSON object.")
    logger.info("trigger_pipeline.start keys=%s", sorted(payload.keys()))
    incident_id = await start_pipeline(payload)
    logger.info("trigger_pipeline.complete incident_id=%s", incident_id)
    return success_response({"incident_id": incident_id, "status": "pipeline_started"})

@app.get("/api/incident/{incident_id}")
async def get_incident_status(incident_id: str):
    """
    Returns the current state of the pipeline for a specific incident.
    """
    if not incident_id:
        raise HTTPException(status_code=422, detail="Incident ID is required.")
    logger.info("get_incident_status.start incident_id=%s", incident_id)
    state = get_pipeline_state(incident_id)
    if not state:
        raise HTTPException(status_code=404, detail="Incident not found")
    logger.info("get_incident_status.complete incident_id=%s status=%s", incident_id, state.get("status"))
    return success_response(state)

@app.get("/api/incidents")
async def list_incidents():
    """
    Returns all incidents processed by the system.
    """
    incidents = get_all_incidents()
    logger.info("list_incidents.complete count=%s", len(incidents))
    return success_response(incidents)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
