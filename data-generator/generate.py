import uuid
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import timedelta

import scenarios as sc

OUT_DIR = "out"
RNG = np.random.default_rng(seed=42)

VIEWING_EVENTS_SCHEMA = pa.schema([
    ("event_id", pa.string()),
    ("title_id", pa.string()),
    ("viewer_id", pa.string()),
    ("region", pa.string()),
    ("device_type", pa.string()),
    ("app_version", pa.string()),
    ("session_start", pa.timestamp("s")),
    ("watch_duration_sec", pa.int32()),
    ("total_runtime_sec", pa.int32()),
    ("completion_pct", pa.float32()),
    ("drop_off_point_sec", pa.int32()),
    ("buffering_events", pa.int32()),
    ("timestamp", pa.timestamp("s")),
])


def views_this_hour(peak, hour, half_life):
    """Exponential decay from a peak, with a short ramp-up in hour 0-1."""
    decay = peak * (0.5 ** (hour / half_life))
    ramp = min(1.0, (hour + 1) / 2.0)  
    return max(decay * ramp, 50)


def assign_device_and_version(n, device_share_override=None, version_share_override=None,
                               affected_device=None, affected_app_version=None):
    """
    device_share_override: if set, overrides the probability of `affected_device`
    (all other devices split the remainder proportionally to their normal weights).
    version_share_override: if set, overrides the probability of `affected_app_version`
    among tv sessions specifically (remaining tv versions split the remainder
    proportionally to their normal weights).
    """
    device_names = list(sc.DEVICE_MIX.keys())
    device_probs = list(sc.DEVICE_MIX.values())

    if device_share_override is not None and affected_device in device_names:
        other_total = 1.0 - sc.DEVICE_MIX[affected_device]
        remaining = 1.0 - device_share_override
        device_probs = []
        for name in device_names:
            if name == affected_device:
                device_probs.append(device_share_override)
            else:
                device_probs.append(sc.DEVICE_MIX[name] / other_total * remaining)

    devices = RNG.choice(device_names, size=n, p=device_probs)

    versions = np.full(n, "", dtype=object)
    tv_mask = devices == "tv"
    n_tv = tv_mask.sum()
    if n_tv > 0:
        version_names = list(sc.TV_APP_VERSIONS.keys())
        version_probs = list(sc.TV_APP_VERSIONS.values())
        if version_share_override is not None and affected_app_version in version_names:
            other_total = 1.0 - sc.TV_APP_VERSIONS[affected_app_version]
            remaining = 1.0 - version_share_override
            version_probs = []
            for name in version_names:
                if name == affected_app_version:
                    version_probs.append(version_share_override)
                else:
                    version_probs.append(sc.TV_APP_VERSIONS[name] / other_total * remaining)
        versions[tv_mask] = RNG.choice(version_names, size=n_tv, p=version_probs)
    return devices, versions


def generate_hour_rows(title_id, region, hour, session_start_base, n_rows,
                        completion_mean, completion_std,
                        buffering_lambda_default,
                        negative_override=None):
    """
    Generate one (title, region, hour) chunk of viewing_events rows.
    negative_override, if provided, applies the anomaly injection logic to the
    subset of rows matching affected_device/affected_app_version.
    """
    devices, versions = assign_device_and_version(
        n_rows,
        device_share_override=negative_override.get("affected_device_share") if negative_override else None,
        version_share_override=negative_override.get("affected_version_share") if negative_override else None,
        affected_device=negative_override.get("affected_device") if negative_override else None,
        affected_app_version=negative_override.get("affected_app_version") if negative_override else None,
    )

    completion = RNG.normal(completion_mean, completion_std, n_rows)
    buffering = RNG.poisson(buffering_lambda_default, n_rows)

    if negative_override is not None:
        affected_mask = (devices == negative_override["affected_device"]) & (
            versions == negative_override["affected_app_version"]
        )
        n_affected = affected_mask.sum()
        if n_affected > 0:
            completion[affected_mask] = RNG.normal(
                negative_override["affected_completion_mean"],
                negative_override["affected_completion_std"],
                n_affected,
            )
            buffering[affected_mask] = RNG.poisson(
                negative_override["affected_buffering_lambda"], n_affected
            )
        
        unaffected_mask = ~affected_mask
        completion[unaffected_mask] *= negative_override["unaffected_dampening"]

    completion = np.clip(completion, 0.01, 1.0)
    watch_duration = (completion * sc.RUNTIME_SEC).astype(np.int32)
    drop_off = np.where(
        completion < 0.98, watch_duration, sc.RUNTIME_SEC
    ).astype(np.int32)
    buffering = np.clip(buffering, 0, None).astype(np.int32)

    session_offsets = RNG.integers(0, 3600, n_rows)  # spread within the hour
    session_start = [session_start_base + timedelta(seconds=int(o)) for o in session_offsets]

    df = pd.DataFrame({
        "event_id": [str(uuid.uuid4()) for _ in range(n_rows)],
        "title_id": title_id,
        "viewer_id": [str(uuid.uuid4()) for _ in range(n_rows)],
        "region": region,
        "device_type": devices,
        "app_version": versions,
        "session_start": session_start,
        "watch_duration_sec": watch_duration,
        "total_runtime_sec": sc.RUNTIME_SEC,
        "completion_pct": completion.astype(np.float32),
        "drop_off_point_sec": drop_off,
        "buffering_events": buffering,
        "timestamp": session_start,
    })
    return df


def generate_title_events(title_cfg, window_hours, out_path,
                           negative_anomaly=None, positive_anomaly=None):
    writer = None
    total_rows = 0
    release_dt = title_cfg["release_datetime"]

    for hour in range(window_hours):
        hour_start_dt = release_dt + timedelta(hours=hour)
        for region in sc.REGIONS:
            base_rate = views_this_hour(
                title_cfg["peak_views_per_hour"], hour, title_cfg["decay_half_life_hours"]
            )

            neg_override = None
            if (negative_anomaly is not None
                    and region == negative_anomaly["region"]
                    and negative_anomaly["hour_start"] <= hour <= negative_anomaly["hour_end"]):
                neg_override = negative_anomaly

            if (positive_anomaly is not None
                    and region == positive_anomaly["region"]
                    and positive_anomaly["hour_start"] <= hour <= positive_anomaly["hour_end"]):
                base_rate *= positive_anomaly["volume_multiplier"]

            n_rows = int(RNG.poisson(base_rate))
            if n_rows <= 0:
                continue

            df = generate_hour_rows(
                title_id=title_cfg["title_id"],
                region=region,
                hour=hour,
                session_start_base=hour_start_dt,
                n_rows=n_rows,
                completion_mean=sc.BASELINE_COMPLETION_MEAN,
                completion_std=sc.BASELINE_COMPLETION_STD,
                buffering_lambda_default=(
                    negative_anomaly["normal_buffering_lambda"] if negative_anomaly else 0.15
                ),
                negative_override=neg_override,
            )
            table = pa.Table.from_pandas(df, schema=VIEWING_EVENTS_SCHEMA, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(out_path, VIEWING_EVENTS_SCHEMA)
            writer.write_table(table)
            total_rows += n_rows

    if writer is not None:
        writer.close()
    return total_rows


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)

    # --- titles.parquet ---
    titles_rows = []
    for t in sc.COMPARABLE_TITLES:
        titles_rows.append({
            "title_id": t["title_id"],
            "title_name": t["title_name"],
            "genre": sc.GENRE,
            "release_type": "streaming",
            "release_datetime": t["release_datetime"],
            "regions": sc.REGIONS,
            "budget_usd": 40_000_000,
            "runtime_min": sc.RUNTIME_SEC // 60,
            "marketing_spend_usd": 10_000_000,
            "is_comparable": 1,
        })
    titles_rows.append({
        "title_id": sc.DEMO_TITLE["title_id"],
        "title_name": sc.DEMO_TITLE["title_name"],
        "genre": sc.GENRE,
        "release_type": "streaming",
        "release_datetime": sc.DEMO_TITLE["release_datetime"],
        "regions": sc.REGIONS,
        "budget_usd": 90_000_000,
        "runtime_min": sc.RUNTIME_SEC // 60,
        "marketing_spend_usd": 35_000_000,
        "is_comparable": 0,
    })
    titles_df = pd.DataFrame(titles_rows)
    titles_df.to_parquet(f"{OUT_DIR}/titles.parquet", index=False)
    print(f"titles.parquet written: {len(titles_df)} rows")

 
    grand_total = 0
    for t in sc.COMPARABLE_TITLES:
        n = generate_title_events(
            t, sc.COMPARABLE_WINDOW_HOURS, f"{OUT_DIR}/events_{t['title_id']}.parquet"
        )
        print(f"{t['title_id']}: {n:,} viewing_events rows")
        grand_total += n

    # --- demo title's viewing_events (with injected anomalies) ---
    n_demo = generate_title_events(
        sc.DEMO_TITLE, sc.DEMO_WINDOW_HOURS, f"{OUT_DIR}/events_{sc.DEMO_TITLE['title_id']}.parquet",
        negative_anomaly=sc.NEGATIVE_ANOMALY,
        positive_anomaly=sc.POSITIVE_ANOMALY,
    )
    print(f"{sc.DEMO_TITLE['title_id']}: {n_demo:,} viewing_events rows")
    grand_total += n_demo

    print(f"\nTOTAL viewing_events rows generated: {grand_total:,}")


if __name__ == "__main__":
    main()
