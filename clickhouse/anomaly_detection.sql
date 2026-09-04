WITH current_metrics AS (
    SELECT
        v.region AS region,
        dateDiff('hour', t.release_datetime, toStartOfHour(v.timestamp)) AS hour_since_release,
        count(*) AS views_this_hour,
        avg(v.completion_pct) AS avg_completion_pct
    FROM dailies.viewing_events v
    INNER JOIN dailies.titles t ON v.title_id = t.title_id
    WHERE v.title_id = {title_id:String}
    GROUP BY region, hour_since_release
)
SELECT
    cm.region,
    cm.hour_since_release,
    cm.views_this_hour,
    round(cm.avg_completion_pct, 4) AS avg_completion_pct,
    round(bp.p25_views_per_hour, 1) AS p25_views_per_hour,
    round(bp.p50_views_per_hour, 1) AS p50_views_per_hour,
    round(bp.p75_views_per_hour, 1) AS p75_views_per_hour,
    round(bp.p50_completion_pct, 4) AS p50_completion_pct,
    (SELECT release_datetime FROM dailies.titles WHERE title_id = {title_id:String}) AS release_datetime,
    multiIf(
        cm.avg_completion_pct < bp.p50_completion_pct * 0.7, 'negative_completion_anomaly',
        cm.views_this_hour < bp.p25_views_per_hour, 'negative_volume_anomaly',
        cm.views_this_hour > bp.p75_views_per_hour * 1.4, 'positive_volume_anomaly',
        'normal'
    ) AS anomaly_type
FROM current_metrics cm
INNER JOIN dailies.baseline_pacing bp
    ON bp.genre = (SELECT genre FROM dailies.titles WHERE title_id = {title_id:String})
   AND bp.region = cm.region
   AND bp.hour_since_release = cm.hour_since_release
WHERE anomaly_type != 'normal'
ORDER BY region, hour_since_release;