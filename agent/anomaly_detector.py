import os

ANOMALY_SQL_PATH = os.path.join(os.path.dirname(__file__), "..", "clickhouse", "anomaly_detection.sql")


def load_anomaly_sql(title_id: str) -> str:
    with open(ANOMALY_SQL_PATH) as f:
        sql = f.read()
    no_comments = "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))
    sql = no_comments.replace("{title_id:String}", f"'{title_id}'")
    return sql.strip().rstrip(";")


def detect_anomalies(run_query, title_id: str, min_consecutive_hours: int = 2) -> list[dict]:
    sql = load_anomaly_sql(title_id)
    rows = run_query(sql)
    rows.sort(key=lambda r: (r["region"], r["anomaly_type"], int(r["hour_since_release"])))

    windows = []
    current = None
    for row in rows:
        region = row["region"]
        atype = row["anomaly_type"]
        hour = int(row["hour_since_release"])

        if (current is not None
                and current["region"] == region
                and current["anomaly_type"] == atype
                and hour == current["window_end_hour"] + 1):
            current["window_end_hour"] = hour
            current["rows"].append(row)
        else:
            if current is not None:
                windows.append(current)
            current = {
                "region": region,
                "anomaly_type": atype,
                "window_start_hour": hour,
                "window_end_hour": hour,
                "rows": [row],
            }
    if current is not None:
        windows.append(current)

    consolidated = []
    for w in windows:
        span = w["window_end_hour"] - w["window_start_hour"] + 1
        if span < min_consecutive_hours:
            continue

        is_completion = "completion" in w["anomaly_type"]
        first_row = w["rows"][0]
        worst_row = (
            min(w["rows"], key=lambda r: float(r["avg_completion_pct"]))
            if is_completion
            else max(w["rows"], key=lambda r: float(r["views_this_hour"]))
        )

        anomaly_id = f"anom_{len(consolidated) + 1:03d}"
        consolidated.append({
            "anomaly_id": anomaly_id,
            "anomaly_type": w["anomaly_type"],
            "region": w["region"],
            "metric": "avg_completion_pct" if is_completion else "views_this_hour",
            "window_start_hour": w["window_start_hour"],
            "window_end_hour": w["window_end_hour"],
            "observed_value": float(
                worst_row["avg_completion_pct"] if is_completion else worst_row["views_this_hour"]
            ),
            "baseline_range": {
                "p25_views_per_hour": float(first_row["p25_views_per_hour"]),
                "p50_views_per_hour": float(first_row["p50_views_per_hour"]),
                "p75_views_per_hour": float(first_row["p75_views_per_hour"]),
                "p50_completion_pct": float(first_row["p50_completion_pct"]),
            },
            "hourly_detail": w["rows"],
        })
    return consolidated
