import os
import sys
import json
import clickhouse_connect

sys.path.insert(0, os.path.abspath("../agent"))
from config import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, require_clickhouse, require_google  # noqa: E402
from db_adapters import clickhouse_connect_adapter  
from controller import InvestigationController  


def main():
    require_clickhouse()
    require_google()

    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST, username=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
        secure=True, port=8443,
    )
    run_query = clickhouse_connect_adapter(client)

    ctrl = InvestigationController(run_query, "orbital_ash")

    print("=" * 70)
    print("STAGE 1: OBSERVE (deterministic, no LLM)")
    print("=" * 70)
    anomalies = ctrl.observe()
    print(f"Found {len(anomalies)} anomalies.")
    latam = next(a for a in anomalies if a["region"] == "LATAM")
    print(json.dumps({k: v for k, v in latam.items() if k != "hourly_detail"}, indent=2))

    input("\nPress Enter to run INVESTIGATE (live Gemini + MCP call)...")
    print("=" * 70)
    print("STAGE 2: INVESTIGATE")
    print("=" * 70)
    evidence_ids = ctrl.investigate(latam)
    print(f"\nCreated {len(evidence_ids)} evidence entries: {evidence_ids}")
    for eid in evidence_ids:
        entry = next(e for e in ctrl.evidence_log if e["id"] == eid)
        print(f"\n--- {eid} ---")
        print("SQL:", entry["sql"])
        print("Result (truncated):", str(entry["result_sample"])[:500])

    if not evidence_ids:
        print("\n*** WARNING: no evidence entries were created. This means")
        print("*** run_agent_with_tool_calls() didn't recognize any tool calls...")
        print("*** the tool_calls list came back empty even though the agent")
        print("*** likely did call run_query internally. Stop here and report")
        print("*** this back rather than continuing to HYPOTHESIZE with no evidence.")
        return

    input("\nPress Enter to run HYPOTHESIZE (live Gemini call, no tools)...")
    print("=" * 70)
    print("STAGE 3: HYPOTHESIZE")
    print("=" * 70)
    hypotheses = ctrl.hypothesize(latam, evidence_ids)
    for h in hypotheses:
        print(f"\n{h['hypothesis_id']}: {h['text']}")

    input("\nPress Enter to run VERIFY on each hypothesis (live Gemini + MCP calls)...")
    print("=" * 70)
    print("STAGE 4: VERIFY")
    print("=" * 70)
    for h in hypotheses:
        result = ctrl.verify(latam, h)
        print(f"\n{h['hypothesis_id']} -> {result['verdict']}")

    input("\nPress Enter to run BRIEF (live Gemini call, structured output)...")
    print("=" * 70)
    print("STAGE 5: BRIEF")
    print("=" * 70)
    result = ctrl.brief()
    print(json.dumps(result["brief"], indent=2))
    if result["validation_problems"]:
        print("\n*** VALIDATION PROBLEMS ***")
        for p in result["validation_problems"]:
            print(" -", p)
    else:
        print("\nBrief passed citation validation cleanly.")


if __name__ == "__main__":
    main()