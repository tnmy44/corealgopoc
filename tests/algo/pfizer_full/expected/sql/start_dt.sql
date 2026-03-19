-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    CAST(CREATE_TIMESTAMP AS TIMESTAMP) AS START_DT
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT START_DT FROM metrics_joined
