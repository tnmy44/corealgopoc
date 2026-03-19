-- Source: deterministic match from star_schema_pipeline
WITH
metrics_joined AS (
  SELECT
    TRIM(RAP_RCPMS_IND) AS RAP_RCPMS_FLAG
  FROM operational_metrics AS om
  LEFT JOIN trial_master AS tm ON TRIM(om.STUDY_NUMBER) = TRIM(tm.TRIAL_NUMBER)
)
SELECT RAP_RCPMS_FLAG FROM metrics_joined
