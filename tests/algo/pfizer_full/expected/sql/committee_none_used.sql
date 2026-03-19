-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    CAST(NULL AS VARCHAR) AS COMMITTEE_NONE_USED
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT COMMITTEE_NONE_USED FROM metrics_joined
