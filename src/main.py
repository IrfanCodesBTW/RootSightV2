import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .features.memory.memory_module import seed_historical_incidents
from .features.orchestrator.pipeline_orchestrator import (
    get_all_incidents,
    get_pipeline_state,
    start_pipeline,
)
from .utils.api_response import error_response, success_response
from .utils.config import settings
from .utils.database import create_db_and_tables

logger = logging.getLogger(__name__)
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

app = FastAPI(title="RootSight API", version="0.1.0")

# ── CORS ────────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Startup ─────────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    logger.info("startup.begin")
    create_db_and_tables()
    await seed_historical_incidents()
    logger.info("startup.complete")


# ── Upload payload helpers ──────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {".json", ".txt", ".log"}


def _normalize_upload_payload(bundle: dict[str, Any], filename: str) -> dict[str, Any]:
    if "alert" in bundle and isinstance(bundle["alert"], dict):
        alert = dict(bundle["alert"])
        payload: dict[str, Any] = {
            "title": alert.get("title") or f"Manual upload: {filename}",
            "service": alert.get("service") or "unknown",
            "severity": alert.get("severity") or "P2",
            "environment": alert.get("environment") or "production",
            "region": alert.get("region") or "us-east-1",
            "source": alert.get("source") or "manual_upload",
            "description": alert.get("description") or f"Uploaded bundle {filename}",
            "started_at": alert.get("started_at") or datetime.now(timezone.utc).isoformat(),
        }
        logs = bundle.get("logs", [])
        if isinstance(logs, list):
            payload["logs"] = logs
        return payload

    return bundle


def _text_upload_payload(filename: str, contents: bytes) -> dict[str, Any]:
    lines = contents.decode("utf-8").splitlines()
    now = datetime.now(timezone.utc).isoformat()

    return {
        "title": f"Manual upload: {filename}",
        "service": "unknown",
        "severity": "P2",
        "environment": "production",
        "region": "us-east-1",
        "source": "manual_upload",
        "description": f"Uploaded bundle {filename}",
        "started_at": now,
        "logs": [
            {
                "timestamp": now,
                "level": "ERROR",
                "message": line,
                "service": "unknown",
                "host": "manual",
            }
            for line in lines
            if line.strip()
        ],
    }


# ── Exception handlers ──────────────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("request_validation_failed path=%s errors=%s", request.url.path, exc.errors())
    return JSONResponse(status_code=422, content=error_response("Invalid request payload.", 422))


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    message = str(exc.detail) if exc.detail else "Request failed."
    logger.error("http_exception path=%s status=%s detail=%s", request.url.path, exc.status_code, message)
    return JSONResponse(status_code=exc.status_code, content=error_response(message, exc.status_code))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("global_exception path=%s error=%s", request.url.path, exc, exc_info=True)
    return JSONResponse(status_code=500, content=error_response("Internal server error.", 500))


# ── Routes ──────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return success_response({"message": "RootSight API is operational", "version": "0.1.0"})


@app.get("/health")
async def health():
    return success_response({"status": "healthy", "version": "0.1.0"})


@app.post("/trigger")
@app.post("/api/trigger")
async def trigger_pipeline(payload: dict[str, Any]):
    if not isinstance(payload, dict) or not payload:
        raise HTTPException(status_code=422, detail="Payload must be a non-empty JSON object.")

    logger.info("trigger_pipeline.start keys=%s", sorted(payload.keys()))
    incident_id = await start_pipeline(payload)
    logger.info("trigger_pipeline.complete incident_id=%s", incident_id)
    return success_response({"incident_id": incident_id, "status": "pipeline_started"})


# Support both singular and plural paths for incident retrieval
@app.get("/incident/{incident_id}")
@app.get("/api/incident/{incident_id}")
@app.get("/incidents/{incident_id}")
@app.get("/api/incidents/{incident_id}")
async def get_incident_status(incident_id: str):
    if not incident_id:
        raise HTTPException(status_code=422, detail="Incident ID is required.")

    logger.info("get_incident_status.start incident_id=%s", incident_id)
    state = get_pipeline_state(incident_id)
    if not state:
        raise HTTPException(status_code=404, detail="Incident not found")

    logger.info("get_incident_status.complete incident_id=%s status=%s", incident_id, state.get("status"))
    return success_response(state)


@app.post("/incident/upload")
@app.post("/api/incident/upload")
async def upload_bundle(file: UploadFile = File(...)):
    # Validate file extension
    filename = (file.filename or "upload.txt").lower()
    ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content=error_response(
                f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}", 400
            ),
        )

    contents = await file.read()

    try:
        if filename.endswith(".json"):
            parsed = json.loads(contents)
            if not isinstance(parsed, dict):
                raise ValueError("JSON bundle must contain an object at the top level.")
            payload = _normalize_upload_payload(parsed, file.filename or "upload.json")
        else:
            payload = _text_upload_payload(file.filename or "upload.txt", contents)
    except Exception as exc:
        return JSONResponse(
            status_code=400,
            content=error_response(f"Cannot parse file: {exc}", 400),
        )

    incident_id = await start_pipeline(payload)
    return success_response({"incident_id": incident_id, "status": "pipeline_started"})


@app.post("/incident/{incident_id}/draft-script")
@app.post("/api/incident/{incident_id}/draft-script")
async def draft_recovery_script(incident_id: str):
    state = get_pipeline_state(incident_id)
    if not state or not state.get("rca"):
        raise HTTPException(status_code=400, detail="RCA data is required to draft a script.")

    from .features.action.action_module import draft_recovery_script_action

    try:
        script = await draft_recovery_script_action(incident_id, state["incident"], state["rca"])
        return success_response({"script": script})
    except Exception:
        return JSONResponse(
            status_code=500,
            content=error_response("Failed to generate recovery script.", 500),
        )


@app.get("/incidents")
@app.get("/api/incidents")
async def list_incidents(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
):
    result = get_all_incidents(page=page, limit=limit)
    logger.info("list_incidents.complete total=%s page=%s", result["total"], page)
    return success_response(result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
