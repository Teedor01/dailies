import sys
sys.path.insert(0, "../agent")
from query_safety import validate_sql, enforce_limit

PASS_CASES = [
    "SELECT * FROM dailies.viewing_events WHERE title_id = 'orbital_ash' LIMIT 10",
    "SELECT region, count(*) FROM viewing_events GROUP BY region",
    """WITH x AS (SELECT region, avg(completion_pct) AS c FROM dailies.viewing_events GROUP BY region)
       SELECT * FROM x WHERE c < 0.5""",
    "select region from dailies.viewing_events limit 5",  
]

FAIL_CASES = [
    ("DROP TABLE dailies.viewing_events", "destructive DROP"),
    ("DELETE FROM dailies.viewing_events WHERE region = 'LATAM'", "destructive DELETE"),
    ("INSERT INTO dailies.viewing_events VALUES (1,2,3)", "mutation INSERT"),
    ("UPDATE dailies.viewing_events SET completion_pct = 1.0", "mutation UPDATE"),
    ("SELECT * FROM dailies.viewing_events; DROP TABLE dailies.titles", "multi-statement injection"),
    ("SELECT * FROM system.users", "system table access"),
    ("SELECT * FROM information_schema.tables", "information_schema access"),
    ("SELECT * FROM dailies.viewing_events v JOIN some_other_db.secret_table s ON v.title_id = s.id",
     "table outside allowed dataset"),
    ("CREATE TABLE evil (x Int32)", "DDL CREATE"),
    ("ALTER TABLE dailies.viewing_events DELETE WHERE 1=1", "ALTER + implicit DELETE"),
    ("", "empty query"),
    ("   ", "whitespace-only query"),
    ("SHOW TABLES", "non-SELECT/WITH statement type"),
    ("GRANT SELECT ON dailies.* TO some_user", "privilege escalation attempt"),
    ("SELECT sleepEachRow(1) FROM numbers(1000000000)", "not blocked by keyword list -- see note below"),
]

def run():
    failures = []

    print("=== PASS cases (should be approved) ===")
    for sql in PASS_CASES:
        ok, reason = validate_sql(sql)
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {reason} :: {sql[:60].strip()}...")
        if not ok:
            failures.append(f"Expected PASS but got REJECT: {sql}")

    print("\n=== FAIL cases (should be rejected) ===")
    for sql, label in FAIL_CASES:
        ok, reason = validate_sql(sql)
       
        if label.startswith("not blocked"):
            status = "KNOWN GAP" if ok else "OK (unexpectedly caught)"
            print(f"[{status}] {label} :: reason={reason}")
            continue
        status = "OK" if not ok else "FAIL"
        print(f"[{status}] {label} :: reason={reason}")
        if ok:
            failures.append(f"Expected REJECT ({label}) but got APPROVED: {sql}")

    print("\n=== enforce_limit behavior ===")
    print(enforce_limit("SELECT * FROM dailies.viewing_events WHERE title_id = 'x'"))
    print(enforce_limit("SELECT * FROM dailies.viewing_events LIMIT 50"))
    print(enforce_limit("SELECT region, count(*) FROM dailies.viewing_events GROUP BY region"))

    print("\n=== RESULT ===")
    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    else:
        print("All safety tests passed.")

if __name__ == "__main__":
    run()
