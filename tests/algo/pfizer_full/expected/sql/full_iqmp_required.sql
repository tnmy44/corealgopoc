-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(IQMP_FULL_FLAG) AS FULL_IQMP_REQUIRED
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT FULL_IQMP_REQUIRED FROM metrics_joined
