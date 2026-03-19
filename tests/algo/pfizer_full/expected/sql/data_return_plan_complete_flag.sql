-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(DATA_RETURN_COMPLETE) AS DATA_RETURN_PLAN_COMPLETE_FLAG
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT DATA_RETURN_PLAN_COMPLETE_FLAG FROM metrics_joined
