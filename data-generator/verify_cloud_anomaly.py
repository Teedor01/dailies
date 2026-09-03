import os
import sys
import json
import clickhouse_connect

sys.path.insert(0, os.path.abspath("../agent"))
from config import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, require_clickhouse 
from db_adapters import clickhouse_connect_adapter  
from anomaly_detector import detect_anomalies  


def main():
    require_clickhouse()
    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST, username=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
        secure=True, port=8443,
    )
    run_query = clickhouse_connect_adapter(client)

    anomalies = detect_anomalies(run_query, "orbital_ash")
    print(f"Found {len(anomalies)} anomaly window(s):\n")
    for a in anomalies:
        a_copy = dict(a)
        a_copy.pop("hourly_detail", None)
        print(json.dumps(a_copy, indent=2))
        print()

    expected = {("LATAM", "negative_completion_anomaly"), ("APAC", "positive_volume_anomaly")}
    found = {(a["region"], a["anomaly_type"]) for a in anomalies}
    if found == expected:
        print("MATCH: identical to the local chdb verification result.")
    else:
        print(f"MISMATCH -- expected {expected}, got {found}")


if __name__ == "__main__":
    main()
