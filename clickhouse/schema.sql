CREATE DATABASE IF NOT EXISTS dailies;

CREATE TABLE IF NOT EXISTS dailies.titles (
    title_id String,
    title_name String,
    genre String,
    release_type Enum8('theatrical' = 1, 'streaming' = 2),
    release_datetime DateTime,
    regions Array(String),
    budget_usd UInt32,
    runtime_min UInt16,
    marketing_spend_usd UInt32,
    is_comparable UInt8            
) ENGINE = MergeTree
ORDER BY title_id;

CREATE TABLE IF NOT EXISTS dailies.viewing_events (
    event_id UUID,
    title_id String,
    viewer_id String,
    region String,
    device_type Enum8('mobile' = 1, 'tv' = 2, 'web' = 3, 'tablet' = 4, 'console' = 5),
    app_version String,
    session_start DateTime,
    watch_duration_sec UInt32,
    total_runtime_sec UInt32,
    completion_pct Float32,
    drop_off_point_sec Nullable(UInt32),
    buffering_events UInt16,
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toDate(timestamp)
ORDER BY (title_id, region, timestamp);

CREATE TABLE IF NOT EXISTS dailies.engagement_events (
    event_id UUID,
    title_id String,
    viewer_id String,
    event_type Enum8('rewind' = 1, 'pause' = 2, 'skip_intro' = 3, 'share' = 4, 'add_to_watchlist' = 5, 'rate' = 6),
    region String,
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toDate(timestamp)
ORDER BY (title_id, region, timestamp);

CREATE TABLE IF NOT EXISTS dailies.social_signals (
    signal_id UUID,
    title_id String,
    platform Enum8('x' = 1, 'reddit' = 2, 'instagram' = 3, 'tiktok' = 4),
    region String,
    sentiment_score Float32,   -- -1.0 .. 1.0
    volume UInt32,
    sample_text String,
    timestamp DateTime
) ENGINE = MergeTree
PARTITION BY toDate(timestamp)
ORDER BY (title_id, region, timestamp);


CREATE TABLE IF NOT EXISTS dailies.baseline_pacing (
    genre String,
    region String,
    hour_since_release UInt16,
    p25_views_per_hour Float32,
    p50_views_per_hour Float32,
    p75_views_per_hour Float32,
    p50_completion_pct Float32
) ENGINE = MergeTree
ORDER BY (genre, region, hour_since_release);
