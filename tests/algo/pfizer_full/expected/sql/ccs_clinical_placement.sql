-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(CLINICAL_PLACEMENT) AS CCS_CLINICAL_PLACEMENT
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT CCS_CLINICAL_PLACEMENT FROM metrics_joined
