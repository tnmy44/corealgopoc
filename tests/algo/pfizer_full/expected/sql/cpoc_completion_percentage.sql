-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    CAST(CPOC_PERCENT_COMPLETE AS DOUBLE) AS CPOC_COMPLETION_PERCENTAGE
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT CPOC_COMPLETION_PERCENTAGE FROM metrics_joined
