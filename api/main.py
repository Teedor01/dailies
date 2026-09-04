import asyncio
import json
import os
import sys
import threading
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.abspath("../agent"))
import clickhouse_connect 
from config import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, require_clickhouse  
from db_adapters import clickhouse_connect_adapter  
from controller import InvestigationController  

app = FastAPI(title="Dailies API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

STEP_ORDER = ["OBSERVE", "INVESTIGATE", "HYPOTHESIZE", "VERIFY", "BRIEF"]


_lock = threading.Lock()
_investigations: dict[str, dict] = {}
_subscribers: dict[str, list[asyncio.Queue]] = {}
_main_loop: Optional[asyncio.AbstractEventLoop] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_investigation_record(investigation_id: str, title_id: str) -> dict:
    return {
        "id": investigation_id,
        "title_id": title_id,
        "status": "running",  
        "created_at": _now(),
        "updated_at": _now(),
        "steps": {name: {"status": "pending", "data": None} for name in STEP_ORDER},
        "anomalies": [],
        "brief": None,
        "validation_problems": [],
        "evidence_log": [],
        "events": [],
        "error": None,
    }


def _public_view(record: dict) -> dict:
    """Investigation summary without the full event/evidence payload... used
    for list endpoints so they stay small."""
    return {k: v for k, v in record.items() if k not in ("events", "evidence_log")}


def _broadcast(investigation_id: str, event: dict):
    """Called from the background PIPELINE THREAD, not the event loop...
    asyncio.Queue.put_nowait() is not thread-safe to call directly from
    another thread, hence call_soon_threadsafe()."""
    with _lock:
        record = _investigations.get(investigation_id)
        if record is not None:
            record["events"].append(event)
            record["updated_at"] = _now()
        subs = list(_subscribers.get(investigation_id, []))
    if _main_loop is not None:
        for q in subs:
            _main_loop.call_soon_threadsafe(q.put_nowait, event)


def _run_pipeline(investigation_id: str, title_id: str):
    """Runs on a background thread. Owns the whole investigation lifecycle:
    connect to ClickHouse, build the controller, run it, record the result."""
    try:
        require_clickhouse()
        client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST, username=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
            secure=True, port=8443,
        )
        run_query = clickhouse_connect_adapter(client)

        controller_holder = {}  # populated below; on_event closes over this,
                                  # not over `controller` directly, so it never
                                  # references the name before assignment

        def on_event(step: str, payload: dict):
            with _lock:
                record = _investigations[investigation_id]
                step_state = record["steps"].get(step)
                if step_state is not None:
                    status = payload.get("status")
                    if status == "running":
                        step_state["status"] = "in_progress"
                        step_state["started_at"] = _now()
                    elif status in ("done", "retrying"):
                        step_state["status"] = "complete" if status == "done" else "in_progress"
                        if status == "done":
                            step_state["completed_at"] = _now()
                    step_state["data"] = payload
                if "controller" in controller_holder:
                    record["evidence_log"] = list(controller_holder["controller"].evidence_log)
                    record["anomalies"] = getattr(controller_holder["controller"], "_last_anomalies", record["anomalies"])

            _broadcast(investigation_id, {"step": step, "payload": payload, "timestamp": _now()})

        controller = InvestigationController(run_query, title_id, on_event=on_event)
        controller_holder["controller"] = controller

        result = controller.run_full_investigation()

        with _lock:
            record = _investigations[investigation_id]
            record["status"] = "complete"
            record["brief"] = result["brief"]
            record["validation_problems"] = result.get("validation_problems", [])
            record["evidence_log"] = controller.evidence_log

        _broadcast(investigation_id, {"step": "PIPELINE", "payload": {"status": "complete"}, "timestamp": _now()})

    except Exception as e:
        with _lock:
            record = _investigations.get(investigation_id)
            if record is not None:
                record["status"] = "error"
                record["error"] = str(e)
        _broadcast(investigation_id, {"step": "PIPELINE", "payload": {"status": "error", "error": str(e)}, "timestamp": _now()})


@app.on_event("startup")
async def _startup():
    global _main_loop
    _main_loop = asyncio.get_running_loop()



class StartInvestigationRequest(BaseModel):
    title_id: str = "orbital_ash"


@app.post("/investigations")
def start_investigation(req: StartInvestigationRequest):
    investigation_id = str(uuid.uuid4())
    with _lock:
        _investigations[investigation_id] = _new_investigation_record(investigation_id, req.title_id)
        _subscribers[investigation_id] = []
    thread = threading.Thread(target=_run_pipeline, args=(investigation_id, req.title_id), daemon=True)
    thread.start()
    return {"investigation_id": investigation_id, "status": "started"}


@app.get("/investigations")
def list_investigations():
    with _lock:
        return [_public_view(rec) for rec in _investigations.values()]


@app.get("/investigations/{investigation_id}")
def get_investigation(investigation_id: str):
    with _lock:
        record = _investigations.get(investigation_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Investigation not found")
        return record


@app.get("/investigations/{investigation_id}/events")
async def stream_events(investigation_id: str):
    """SSE stream. Replays everything that already happened before this
    client connected, then streams live. Closes itself when the pipeline
    reports complete/error... clients should reconnect if they need more."""
    with _lock:
        if investigation_id not in _investigations:
            raise HTTPException(status_code=404, detail="Investigation not found")
        q: asyncio.Queue = asyncio.Queue()
        _subscribers.setdefault(investigation_id, []).append(q)
        backlog = list(_investigations[investigation_id]["events"])

    async def event_generator():
        try:
            already_finished = False
            for event in backlog:
                yield f"data: {json.dumps(event, default=str)}\n\n"
                if event.get("step") == "PIPELINE" and event.get("payload", {}).get("status") in ("complete", "error"):
                    already_finished = True
            if already_finished:
                return
            while True:
                event = await q.get()
                yield f"data: {json.dumps(event, default=str)}\n\n"
                if event.get("step") == "PIPELINE" and event.get("payload", {}).get("status") in ("complete", "error"):
                    break
        finally:
            with _lock:
                subs = _subscribers.get(investigation_id)
                if subs and q in subs:
                    subs.remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")



@app.get("/evidence")
def search_evidence(
    investigation_id: Optional[str] = None,
    entry_type: Optional[str] = None,
    step: Optional[str] = None,
    q: Optional[str] = None,
):
    with _lock:
        results = []
        for inv_id, rec in _investigations.items():
            if investigation_id and inv_id != investigation_id:
                continue
            for entry in rec["evidence_log"]:
                if entry_type and entry["entry_type"] != entry_type:
                    continue
                if step and entry["step"] != step:
                    continue
                if q and q.lower() not in (entry.get("claim") or "").lower():
                    continue
                results.append({**entry, "investigation_id": inv_id, "title_id": rec["title_id"]})
        results.sort(key=lambda e: e.get("timestamp", ""))
        return results


@app.get("/evidence/{investigation_id}/{evidence_id}")
def get_evidence_detail(investigation_id: str, evidence_id: str):
    with _lock:
        record = _investigations.get(investigation_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Investigation not found")
        for entry in record["evidence_log"]:
            if entry["id"] == evidence_id:
                return {**entry, "investigation_id": investigation_id, "title_id": record["title_id"]}
        raise HTTPException(status_code=404, detail="Evidence not found")



@app.get("/briefs")
def list_briefs():
    with _lock:
        return [
            {
                "investigation_id": rec["id"],
                "title_id": rec["title_id"],
                "brief": rec["brief"],
                "validation_problems": rec.get("validation_problems", []),
                "created_at": rec["created_at"],
            }
            for rec in _investigations.values()
            if rec["brief"] is not None
        ]



@app.get("/overview")
def overview():
    with _lock:
        investigations = list(_investigations.values())
        total_evidence = sum(len(rec["evidence_log"]) for rec in investigations)
        return {
            "investigation_count": len(investigations),
            "running_count": sum(1 for r in investigations if r["status"] == "running"),
            "complete_count": sum(1 for r in investigations if r["status"] == "complete"),
            "brief_count": sum(1 for r in investigations if r["brief"] is not None),
            "total_evidence_entries": total_evidence,
            "investigations": [_public_view(rec) for rec in investigations],
        }