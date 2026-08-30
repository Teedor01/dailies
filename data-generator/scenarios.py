from datetime import datetime, timedelta

GENRE = "sci_fi"
RUNTIME_SEC = 5400  

REGIONS = ["NA", "EU", "LATAM", "APAC", "MENA"]

DEVICE_MIX = {
    "mobile": 0.35,
    "tv": 0.25,
    "web": 0.20,
    "tablet": 0.12,
    "console": 0.08,
}

TV_APP_VERSIONS = {
    "4.0": 0.30,
    "4.1": 0.35,
    "4.2": 0.35,  
}


NOW = datetime(2026, 8, 1, 12, 0, 0)


COMPARABLE_TITLES = [
    {
        "title_id": "cmp_001",
        "title_name": "Comparable Release Alpha",
        "release_datetime": NOW - timedelta(days=10),
        "peak_views_per_hour": 48000,   # per region, at hour 0
        "decay_half_life_hours": 18,
    },
    {
        "title_id": "cmp_002",
        "title_name": "Comparable Release Beta",
        "release_datetime": NOW - timedelta(days=20),
        "peak_views_per_hour": 40000,
        "decay_half_life_hours": 20,
    },
    {
        "title_id": "cmp_003",
        "title_name": "Comparable Release Gamma",
        "release_datetime": NOW - timedelta(days=30),
        "peak_views_per_hour": 44000,
        "decay_half_life_hours": 16,
    },
]
COMPARABLE_WINDOW_HOURS = 72
BASELINE_COMPLETION_MEAN = 0.68
BASELINE_COMPLETION_STD = 0.10


DEMO_TITLE = {
    "title_id": "orbital_ash",
    "title_name": "Orbital Ash",
    "release_datetime": NOW - timedelta(hours=14),
    "peak_views_per_hour": 50000,
    "decay_half_life_hours": 18,
}
DEMO_WINDOW_HOURS = 14


NEGATIVE_ANOMALY = {
    "region": "LATAM",
    "hour_start": 6,
    "hour_end": 9,         
    "affected_device": "tv",
    "affected_app_version": "4.2",
    "affected_device_share": 0.45,       
    "affected_version_share": 0.55,      
    "affected_completion_mean": 0.05,
    "affected_completion_std": 0.03,
    "affected_buffering_lambda": 5.0,     
    "unaffected_dampening": 0.75,         
    "normal_buffering_lambda": 0.15,
}


POSITIVE_ANOMALY = {
    "region": "APAC",
    "hour_start": 8,
    "hour_end": 11,
    "volume_multiplier": 2.0,
}
