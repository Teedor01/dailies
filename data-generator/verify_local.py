from chdb import session as chs
import time

sess = chs.Session("./chdb_data")

def run_sql_file(path, params=None):
    with open(path) as f:
        sql = f.read()
    if params:
        for k, v in params.items():
            sql = sql.replace(f"{{{k}:String}}", f"'{v}'")
    no_comments = "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))
    raw_statements = [s.strip() for s in no_comments.split(";")]
    results = []
    for stmt in raw_statements:
        if not stmt:
            continue
        results.append(sess.query(stmt, "CSV"))
    return results


print("=== 1. Creating schema ===")
run_sql_file("../clickhouse/schema.sql")
print("schema created OK")

print("\n=== 2. Loading titles.parquet ===")
sess.query("INSERT INTO dailies.titles SELECT * FROM file('out/titles.parquet', Parquet)")
r = sess.query("SELECT count(*) FROM dailies.titles", "CSV")
print("titles row count:", r)

print("\n=== 3. Loading viewing_events (comparables + demo title) ===")
t0 = time.time()
for f in ["events_cmp_001.parquet", "events_cmp_002.parquet", "events_cmp_003.parquet", "events_orbital_ash.parquet"]:
    sess.query(f"INSERT INTO dailies.viewing_events SELECT * FROM file('out/{f}', Parquet)")
    print(f"  loaded {f}")
t1 = time.time()
r = sess.query("SELECT count(*) FROM dailies.viewing_events", "CSV")
print("viewing_events row count:", r, f"(load took {t1-t0:.1f}s)")

print("\n=== 4. Building baseline_pacing from comparable titles ===")
run_sql_file("../clickhouse/baseline_pacing.sql")
r = sess.query("SELECT count(*) FROM dailies.baseline_pacing", "CSV")
print("baseline_pacing row count:", r)
r = sess.query("SELECT * FROM dailies.baseline_pacing WHERE region = 'LATAM' ORDER BY hour_since_release LIMIT 10", "Pretty")
print("sample baseline_pacing rows (LATAM):")
print(r)

print("\n=== 5. Running deterministic anomaly_detection.sql for orbital_ash ===")
result = run_sql_file("../clickhouse/anomaly_detection.sql", params={"title_id": "orbital_ash"})
print(result[-1])

print("\n=== 6. Sanity check: full region/hour breakdown (not just anomalies) ===")
sanity = sess.query("""
    SELECT
        v.region,
        dateDiff('hour', t.release_datetime, toStartOfHour(v.timestamp)) AS hour_since_release,
        count(*) AS views_this_hour,
        round(avg(v.completion_pct), 4) AS avg_completion_pct
    FROM dailies.viewing_events v
    INNER JOIN dailies.titles t ON v.title_id = t.title_id
    WHERE v.title_id = 'orbital_ash'
    GROUP BY v.region, hour_since_release
    ORDER BY v.region, hour_since_release
""", "Pretty")
print(sanity)
