import sys
import time
import json

sys.path.insert(0, ".")
import main as api_main  # noqa: E402
from fastapi.testclient import TestClient


class FakeController:
    def __init__(self, run_query, title_id, on_event=None):
        self.evidence_log = []
        self.on_event = on_event or (lambda s, p: None)
        self.title_id = title_id

    def run_full_investigation(self):
        for step in ["OBSERVE", "INVESTIGATE", "HYPOTHESIZE", "VERIFY", "BRIEF"]:
            self.on_event(step, {"status": "running"})
            self.evidence_log.append({
                "id": f"ev_{len(self.evidence_log)+1:03d}",
                "entry_type": "observed_fact" if step != "HYPOTHESIZE" else "hypothesis",
                "step": step, "claim": f"{step} happened", "sql": "SELECT 1",
                "result_sample": {"x": 1}, "supports": [], "timestamp": "now",
            })
            time.sleep(0.02)
            self.on_event(step, {"status": "done"})
        return {"brief": {"summary": "test summary", "claims": [{"text": "x", "citations": ["ev_001"]}],
                           "rejected_hypotheses": []},
                "validation_problems": []}


api_main.InvestigationController = FakeController
api_main.require_clickhouse = lambda: None
api_main.clickhouse_connect.get_client = lambda **kw: object()
api_main.clickhouse_connect_adapter = lambda client: (lambda sql: [])

client = TestClient(api_main.app)

print("=== POST /investigations ===")
r = client.post("/investigations", json={"title_id": "orbital_ash"})
print(r.status_code, r.json())
investigation_id = r.json()["investigation_id"]

time.sleep(0.5)  

print("\n=== GET /investigations ===")
r = client.get("/investigations")
print(r.status_code, json.dumps(r.json(), indent=2)[:300])

print("\n=== GET /investigations/{id} ===")
r = client.get(f"/investigations/{investigation_id}")
print(r.status_code, "status:", r.json()["status"], "steps:", {k: v["status"] for k, v in r.json()["steps"].items()})

print("\n=== GET /investigations/{id}/events (SSE, should replay backlog) ===")
with client.stream("GET", f"/investigations/{investigation_id}/events") as r:
    print(r.status_code)
    count = 0
    for line in r.iter_lines():
        if line.startswith("data: "):
            count += 1
            evt = json.loads(line[6:])
            print(" ", evt["step"], evt["payload"].get("status"))
            if evt.get("step") == "PIPELINE":
                break
    print(f"Total SSE events replayed: {count}")

print("\n=== GET /evidence ===")
r = client.get("/evidence")
print(r.status_code, len(r.json()), "entries")
print(json.dumps(r.json()[0], indent=2))

print("\n=== GET /evidence?entry_type=hypothesis ===")
r = client.get("/evidence", params={"entry_type": "hypothesis"})
print(r.status_code, len(r.json()), "entries (expected 1)")

print("\n=== GET /evidence/{inv}/{ev_id} ===")
r = client.get(f"/evidence/{investigation_id}/ev_001")
print(r.status_code, r.json()["claim"])

print("\n=== GET /evidence/{inv}/nonexistent (expect 404) ===")
r = client.get(f"/evidence/{investigation_id}/ev_999")
print(r.status_code)

print("\n=== GET /briefs ===")
r = client.get("/briefs")
print(r.status_code, json.dumps(r.json(), indent=2)[:300])

print("\n=== GET /overview ===")
r = client.get("/overview")
print(r.status_code, json.dumps(r.json(), indent=2)[:400])

print("\nALL ENDPOINT TESTS COMPLETED")