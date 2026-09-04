import asyncio
import threading
import time
import sys

sys.path.insert(0, ".")
import main as api_main  # noqa: E402


class FakeController:
    """Mimics InvestigationController's interface without touching any
    real credentials -- just to prove the threading/SSE bridge works."""
    def __init__(self, run_query, title_id, on_event=None):
        self.evidence_log = []
        self.on_event = on_event or (lambda s, p: None)
        self.title_id = title_id

    def run_full_investigation(self):
        for step in ["OBSERVE", "INVESTIGATE", "HYPOTHESIZE", "VERIFY", "BRIEF"]:
            self.on_event(step, {"status": "running"})
            self.evidence_log.append({
                "id": f"ev_{len(self.evidence_log)+1:03d}",
                "entry_type": "observed_fact", "step": step,
                "claim": f"{step} happened", "sql": None,
                "result_sample": None, "supports": [], "timestamp": "now",
            })
            time.sleep(0.05)
            self.on_event(step, {"status": "done"})
        return {"brief": {"summary": "test summary", "claims": [], "rejected_hypotheses": []},
                "validation_problems": []}


api_main.InvestigationController = FakeController
api_main.require_clickhouse = lambda: None
api_main.clickhouse_connect.get_client = lambda **kw: object()
api_main.clickhouse_connect_adapter = lambda client: (lambda sql: [])


async def main():
    await api_main._startup()  

    investigation_id = "test-inv-1"
    with api_main._lock:
        api_main._investigations[investigation_id] = api_main._new_investigation_record(investigation_id, "orbital_ash")
        api_main._subscribers[investigation_id] = []

    q = asyncio.Queue()
    with api_main._lock:
        api_main._subscribers[investigation_id].append(q)


    t = threading.Thread(target=api_main._run_pipeline, args=(investigation_id, "orbital_ash"), daemon=True)
    t.start()

    events_received = []
    while True:
        event = await asyncio.wait_for(q.get(), timeout=5)
        events_received.append(event)
        if event.get("step") == "PIPELINE":
            break

    print(f"Received {len(events_received)} events total (expected 11: 2 per step x 5 steps + 1 PIPELINE)")
    for e in events_received:
        print(" ", e["step"], e["payload"].get("status"))

    with api_main._lock:
        record = api_main._investigations[investigation_id]
    print("final status:", record["status"])
    print("evidence_log length (expected 5):", len(record["evidence_log"]))
    print("brief present:", record["brief"] is not None)
    print("step statuses:", {k: v["status"] for k, v in record["steps"].items()})


asyncio.run(main())