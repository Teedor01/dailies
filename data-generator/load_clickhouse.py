import os
import sys
import time
import pandas as pd
import pyarrow.parquet as pq
import clickhouse_connect
from clickhouse_connect.driver.exceptions import OperationalError

sys.path.insert(0, os.path.abspath("../agent"))
from config import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, require_clickhouse  

OUT_DIR = "out"
CHUNK_ROWS = 50_000
MAX_RETRIES = 5
RETRY_BASE_DELAY = 5


def get_client():
    require_clickhouse()
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST, username=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
        secure=True, port=8443, connect_timeout=30, send_receive_timeout=900,
    )


def run_ddl_file(client, path):
    with open(path) as f:
        sql = f.read()
    no_comments = "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))
    statements = [s.strip() for s in no_comments.split(";") if s.strip()]
    for stmt in statements:
        client.command(stmt)


def insert_with_retry(client, table, df, database="dailies"):
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client.insert_df(table, df, database=database)
            return
        except (OperationalError, TimeoutError) as e:
            last_err = e
            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            print(f"\n    Insert attempt {attempt}/{MAX_RETRIES} failed ({type(e).__name__}). "
                  f"Retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError(f"Insert failed after {MAX_RETRIES} attempts") from last_err


def title_id_from_events_filename(fname: str) -> str:
    return fname[len("events_"):-len(".parquet")]


def loaded_row_count(client, title_id: str) -> int:
    result = client.query(
        "SELECT count(*) FROM dailies.viewing_events WHERE title_id = {tid:String}",
        parameters={"tid": title_id},
    )
    return result.result_rows[0][0]


def delete_title_rows(client, title_id: str):
    print(f"    Removing partially-loaded rows for {title_id} before reloading...")
    client.command(
        "ALTER TABLE dailies.viewing_events DELETE WHERE title_id = {tid:String}",
        parameters={"tid": title_id},
    )
    for _ in range(30):
        if loaded_row_count(client, title_id) == 0:
            return
        time.sleep(2)
    print(f"    Warning: delete for {title_id} may still be finalizing server-side.")


def insert_parquet_in_chunks(client, table, parquet_path):
    pf = pq.ParquetFile(parquet_path)
    total = 0
    t0 = time.time()
    for batch in pf.iter_batches(batch_size=CHUNK_ROWS):
        df = batch.to_pandas()
        insert_with_retry(client, table, df)
        total += len(df)
        elapsed = time.time() - t0
        rate = total / elapsed if elapsed > 0 else 0
        print(f"    ...{total:,} rows inserted ({rate:,.0f} rows/sec)", end="\r")
    print(f"    {total:,} rows inserted into {table} ({time.time()-t0:.1f}s)")
    return total


def main():
    client = get_client()
    print(f"Connected. Server version: {client.server_version}")

    print("\n=== Creating schema ===")
    run_ddl_file(client, "../clickhouse/schema.sql")
    print("Schema created.")

    print("\n=== Loading titles (resume-safe) ===")
    titles_df = pd.read_parquet(f"{OUT_DIR}/titles.parquet")
    existing_titles = client.query("SELECT count(*) FROM dailies.titles").result_rows[0][0]
    if existing_titles == len(titles_df):
        print(f"titles already loaded ({existing_titles} rows) -- skipping.")
    else:
        if existing_titles > 0:
            print(f"Found {existing_titles} existing title rows (expected {len(titles_df)}) -- "
                  f"truncating and reloading to avoid duplicates.")
            client.command("TRUNCATE TABLE dailies.titles")
        client.insert_df("titles", titles_df, database="dailies")
        print(f"{len(titles_df)} title rows inserted.")

    print("\n=== Loading viewing_events (resume-safe, per title_id) ===")
    grand_total = 0
    event_files = sorted(f for f in os.listdir(OUT_DIR) if f.startswith("events_") and f.endswith(".parquet"))
    for fname in event_files:
        title_id = title_id_from_events_filename(fname)
        path = f"{OUT_DIR}/{fname}"
        expected = pq.ParquetFile(path).metadata.num_rows
        actual = loaded_row_count(client, title_id)

        print(f"  {fname} (title_id={title_id}): expected={expected:,}, already loaded={actual:,}")
        if actual == expected:
            print("    Already fully loaded -- skipping.")
            grand_total += actual
            continue
        if actual > 0:
            delete_title_rows(client, title_id)

        grand_total += insert_parquet_in_chunks(client, "viewing_events", path)

    print(f"\nTotal viewing_events rows loaded (this run + previously): {grand_total:,}")

    print("\n=== Building baseline_pacing ===")
    existing_baseline = client.query("SELECT count(*) FROM dailies.baseline_pacing").result_rows[0][0]
    if existing_baseline > 0:
        print(f"baseline_pacing already has {existing_baseline} rows -- truncating and rebuilding.")
        client.command("TRUNCATE TABLE dailies.baseline_pacing")
    run_ddl_file(client, "../clickhouse/baseline_pacing.sql")
    count = client.query("SELECT count(*) FROM dailies.baseline_pacing").result_rows[0][0]
    print(f"baseline_pacing rows: {count}")

    print("\nDone. Verify with:")
    print("  python3 verify_cloud_anomaly.py")


if __name__ == "__main__":
    main()
