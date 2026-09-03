import os
import sys
import json
import clickhouse_connect

sys.path.insert(0, os.path.abspath("../agent"))
from config import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, require_clickhouse, require_google  
from db_adapters import clickhouse_connect_adapter  
from anomaly_detector import detect_anomalies  
from tool_reasoner import build_investigate_agent  
from runner_helpers import run_agent_once   


def main():
    require_clickhouse()
    require_google()

    print("=== Fetching the real anomaly from ClickHouse Cloud (deterministic, no LLM) ===")
    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST, username=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
        secure=True, port=8443,
    )
    run_query = clickhouse_connect_adapter(client)
    anomalies = detect_anomalies(run_query, "orbital_ash")

    latam_anomaly = next(a for a in anomalies if a["region"] == "LATAM")
    latam_anomaly = {k: v for k, v in latam_anomaly.items() if k != "hourly_detail"}
    print(json.dumps(latam_anomaly, indent=2))

    print("\n=== Handing this anomaly to the real investigate_agent (Gemini + MCP) ===")
    print("(This calls the Gemini API and, through it, the real mcp-clickhouse server")
    print(" against your real Cloud data. First live model call in this project.)\n")

    agent = build_investigate_agent()
    prompt = (
        "Here is a confirmed anomaly, detected deterministically (not by you):\n\n"
        f"{json.dumps(latam_anomaly, indent=2)}\n\n"
        "Investigate why this happened. The title_id is 'orbital_ash'."
    )

    response = run_agent_once(agent, prompt)
    print("=== Agent response ===")
    print(response)


if __name__ == "__main__":
    main()
