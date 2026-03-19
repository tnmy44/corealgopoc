-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    CAST(ENROLLMENT_TARGET AS BIGINT) AS PLANNED_PATIENTS
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT PLANNED_PATIENTS FROM metrics_joined
