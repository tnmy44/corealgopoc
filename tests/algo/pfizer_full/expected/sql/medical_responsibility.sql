-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(MEDICAL_OWNER) AS MEDICAL_RESPONSIBILITY
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT MEDICAL_RESPONSIBILITY FROM metrics_joined
