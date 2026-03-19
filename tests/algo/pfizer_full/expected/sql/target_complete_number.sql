-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    CAST(COMPLETION_TARGET AS BIGINT) AS TARGET_COMPLETE_NUMBER
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT TARGET_COMPLETE_NUMBER FROM metrics_joined
