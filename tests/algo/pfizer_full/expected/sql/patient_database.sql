-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(EDC_SYSTEM) AS PATIENT_DATABASE
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT PATIENT_DATABASE FROM metrics_joined
