import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.insert(0, os.path.abspath("../agent"))
from query_safety import validate_sql, enforce_limit  # noqa: E402

CHDB_DATA_PATH = os.path.abspath("./chdb_data")

SERVER_ENV = {
    **os.environ,
    "CLICKHOUSE_ENABLED": "false",   
    "CHDB_ENABLED": "true",
    "CHDB_DATA_PATH": CHDB_DATA_PATH,
    "CLICKHOUSE_MCP_SERVER_TRANSPORT": "stdio",
}

evidence_log = []


def log_evidence(entry_type, step, sql, result_text, claim_text):
    entry = {
        "id": f"ev_{len(evidence_log) + 1:03d}",
        "entry_type": entry_type,
        "step": step,
        "sql": sql,
        "result_sample": result_text[:500] if result_text else None,
        "claim": claim_text,
    }
    evidence_log.append(entry)
    return entry


async def run_query_through_safety_gate(session, sql, step, claim_text):
    print(f"\n--- Proposed SQL ({step}) ---")
    print(sql)

    ok, reason = validate_sql(sql)
    if not ok:
        print(f"REJECTED by query_safety: {reason}")
        return None

    safe_sql = enforce_limit(sql)
    print("APPROVED by query_safety. Calling real MCP tool run_chdb_select_query...")

    result = await session.call_tool("run_chdb_select_query", {"query": safe_sql})
    result_text = result.content[0].text if result.content else ""
    print("MCP result (truncated):", result_text[:400])

    entry = log_evidence("observed_fact", step, safe_sql, result_text, claim_text)
    print(f"Logged as evidence entry {entry['id']}")
    return entry


async def main():
    server_params = StdioServerParameters(
        command="python3",
        args=["-m", "mcp_clickhouse.main"],
        env=SERVER_ENV,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("=== Real MCP tools exposed by the server ===")
            for t in tools.tools:
                print(f"  - {t.name}: {t.description}")

            print("\n=== Step A: list_databases (real MCP call) ===")
            r = await session.call_tool("list_databases", {})
            print(r.content[0].text if r.content else r)

            print("\n=== Step B: list_tables (real MCP call) ===")
            r = await session.call_tool("list_tables", {"database": "dailies"})
            text = r.content[0].text if r.content else ""
            print(text[:800])

            print("\n=== Step C: simulated INVESTIGATE query (safety-gated, real MCP call) ===")

            investigate_sql = """
                SELECT
                    device_type,
                    app_version,
                    count(*) AS sessions,
                    round(avg(completion_pct), 4) AS avg_completion,
                    round(avg(buffering_events), 3) AS avg_buffering
                FROM dailies.viewing_events
                WHERE title_id = 'orbital_ash' AND region = 'LATAM'
                  AND dateDiff('hour',
                        (SELECT release_datetime FROM dailies.titles WHERE title_id = 'orbital_ash'),
                        toStartOfHour(timestamp)) BETWEEN 6 AND 9
                GROUP BY device_type, app_version
                ORDER BY avg_completion ASC
            """
            await run_query_through_safety_gate(
                session, investigate_sql, "INVESTIGATE",
                claim_text="Device/app_version breakdown for LATAM during the anomaly window",
            )

            print("\n=== Step D: rejected query (safety layer should block this BEFORE any MCP call) ===")
            malicious_sql = "DROP TABLE dailies.viewing_events"
            result = await run_query_through_safety_gate(
                session, malicious_sql, "INVESTIGATE",
                claim_text="(should never execute)",
            )
            assert result is None, "SAFETY LAYER FAILED TO BLOCK A DESTRUCTIVE QUERY"
            print("Confirmed: destructive query never reached the MCP server.")

            print("\n=== Step E: rejected query (table outside allowed dataset) ===")
            out_of_scope_sql = "SELECT * FROM system.users"
            result = await run_query_through_safety_gate(
                session, out_of_scope_sql, "INVESTIGATE",
                claim_text="(should never execute)",
            )
            assert result is None, "SAFETY LAYER FAILED TO BLOCK A SYSTEM-TABLE QUERY"
            print("Confirmed: system-table query never reached the MCP server.")

    print("\n=== Final evidence_log ===")
    print(json.dumps(evidence_log, indent=2, default=str)[:2000])


if __name__ == "__main__":
    asyncio.run(main())
