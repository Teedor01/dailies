INSERT INTO dailies.baseline_pacing
SELECT
    genre,
    region,
    hour_since_release,
    quantile(0.25)(views_this_hour) AS p25_views_per_hour,
    quantile(0.50)(views_this_hour) AS p50_views_per_hour,
    quantile(0.75)(views_this_hour) AS p75_views_per_hour,
    avg(avg_completion_pct)         AS p50_completion_pct
FROM (
    SELECT
        t.genre AS genre,
        v.region AS region,
        dateDiff('hour', t.release_datetime, toStartOfHour(v.timestamp)) AS hour_since_release,
        t.title_id AS title_id,
        count(*) AS views_this_hour,
        avg(v.completion_pct) AS avg_completion_pct
    FROM dailies.viewing_events v
    INNER JOIN dailies.titles t ON v.title_id = t.title_id
    WHERE t.is_comparable = 1
    GROUP BY genre, region, hour_since_release, title_id
)
GROUP BY genre, region, hour_since_release;
