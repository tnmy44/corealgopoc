-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    CAST(MONITOR_INTERVAL_MAX AS BIGINT) AS MONITOR_VISIT_PLAN_INTERVAL_MAX
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT MONITOR_VISIT_PLAN_INTERVAL_MAX FROM metrics_joined
