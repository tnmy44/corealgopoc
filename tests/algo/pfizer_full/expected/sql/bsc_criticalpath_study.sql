-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(CRITICAL_PATH_IND) AS BSC_CRITICALPATH_STUDY
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT BSC_CRITICALPATH_STUDY FROM metrics_joined
